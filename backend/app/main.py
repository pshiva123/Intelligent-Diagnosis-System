import sys
import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import joblib
import pandas as pd
import numpy as np
import json
import ssl
from datetime import datetime
from pymongo import MongoClient
import bcrypt
from dotenv import load_dotenv
import razorpay
import shap 
from thefuzz import process
import google.generativeai as genai 
import itertools

# Directory path configurations
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

# Initialize Primary Clinical Interceptor
try:
    from clinical_rules import get_heuristic_diagnosis
    print("INFO: Primary Clinical Interceptor loaded successfully.")
except ImportError as e:
    print(f"WARN: Primary Interceptor unavailable. Operating on strict ML pipeline. Error: {e}")
    def get_heuristic_diagnosis(syms): return None

# Initialize NLP Pipeline
try:
    from app.symptom_nlp import extract_and_map_symptoms
except ImportError:
    def extract_and_map_symptoms(text): return [], "medium"

load_dotenv() 

app = FastAPI(title="Intelligent Ayurvedic Diagnosis API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==========================================
# DATA MODELS
# ==========================================
class UserInput(BaseModel):
    text: str
    username: str
    age_category: str  
    gender: str        
    is_pregnant: bool
    severity: str
    is_final_check: bool = False  

class UserRegister(BaseModel):
    name: str
    password: str
    age: int
    gender: str
    weight: float
    height: float
    digestion: str = "Balanced"
    sleep: str = "Moderate"
    weather: str = "Tolerant"
    frame: str = "Medium"

class UserLogin(BaseModel):
    name: str
    password: str

# ==========================================
# DATABASE & ARTIFACT INITIALIZATION
# ==========================================
MONGO_URI = os.getenv("MONGO_URI")
try:
    client = MongoClient(MONGO_URI)
    db = client["diagnosis_system"] 
    users_collection = db["users"]   
    logs_collection = db["diagnostic_logs"] 
    orders_collection = db["orders"]        
    inventory_collection = db["pharmacy_products_final"]
    print("INFO: Connected to MongoDB Atlas Cluster.")
except Exception as e:
    print(f"ERROR: MongoDB Connection Failed: {e}")

try:
    print("INFO: Loading Multi-Model Ensemble Engine...")
    model = joblib.load(os.path.join(current_dir, "../models/ensemble_model.pkl"))
    xgb_base = joblib.load(os.path.join(current_dir, "../models/xgboost_base_model.pkl"))
    le = joblib.load(os.path.join(current_dir, "../models/label_encoder.pkl"))
    symptoms_list = joblib.load(os.path.join(current_dir, "../models/symptoms_list.pkl"))
    critical_diseases = joblib.load(os.path.join(current_dir, "../models/critical_diseases.pkl"))
    print("INFO: ML Artifacts and Security Protocols Loaded.")
except Exception as e: 
    print(f"ERROR: ML Artifact Load Failure: {e}")
    critical_diseases = ['Heart attack', 'Paralysis (brain hemorrhage)']
    model = xgb_base = le = None
    symptoms_list = [] 

def _normalize_list(value):
    if isinstance(value, str):
        return [value.strip().lower()]
    if isinstance(value, list):
        return [str(v).strip().lower() for v in value if str(v).strip()]
    return []

# YOUR CUSTOM DB BUILDER
def _build_db_from_medicine_master(master_data):
    ages = ["young", "middle", "elder"]
    genders = ["male", "female"]
    severities = ["low", "medium", "high"]
    structured = {}

    for disease, medicines in master_data.items():
        disease_key = str(disease).strip()
        if not disease_key or not isinstance(medicines, list):
            continue
        disease_bucket = {}

        for age, gender, severity in itertools.product(ages, genders, severities):
            combo_key = f"{age}_{gender}_{severity}"
            candidates = []
            for med in medicines:
                if not isinstance(med, dict):
                    continue

                allowed_ages = _normalize_list(med.get("allowed_ages", ["all"]))
                allowed_genders = _normalize_list(med.get("allowed_genders", ["all"]))
                allowed_severities = _normalize_list(med.get("allowed_severities", ["low", "medium", "high"]))

                age_ok = "all" in allowed_ages or age in allowed_ages
                gender_ok = "all" in allowed_genders or gender in allowed_genders
                severity_ok = "all" in allowed_severities or severity in allowed_severities
                if not (age_ok and gender_ok and severity_ok):
                    continue

                candidates.append(
                    {
                        "medicine_name": med.get("medicine_name", "Ayurvedic Protocol"),
                        "dosage": med.get("dosage", "Standard Dose"),
                        "formulation_type": med.get("formulation_type", "classical"),
                        "dosha_type": med.get("dosha_type", "tridosha"),
                        "herb_sanskrit": med.get("herb_sanskrit", []),
                    }
                )
            disease_bucket[combo_key] = candidates
        structured[disease_key] = disease_bucket
    return structured

try:
    kb_path = os.path.join(current_dir, "../ayurveda_pipeline/output/ayurveda_kb_structured.json")
    with open(kb_path, "r", encoding="utf-8") as f:
        ayurveda_db = json.load(f)
    print("INFO: Ayurveda Medical Ontology Indexed from output KB.")
except Exception:
    try:
        master_path = os.path.join(current_dir, "../ayurveda_pipeline/medicine_master.json")
        with open(master_path, "r", encoding="utf-8") as f:
            master_data = json.load(f)
        ayurveda_db = _build_db_from_medicine_master(master_data)
        print("INFO: Ayurveda protocol loaded from medicine_master.json.")
    except Exception as e:
        print(f"WARN: Ayurveda KB unavailable: {e}")
        ayurveda_db = {}

# ==========================================
# GENERATIVE AI PROFILING CONFIGURATION
# ==========================================
try:
    genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
    gemini_model = genai.GenerativeModel('gemini-1.5-flash')
    print("INFO: Generative Profiling API Ready.")
except Exception as e:
    gemini_model = None

def generate_ayurvedic_profile(user_data: UserRegister):
    height_m = user_data.height / 100.0
    bmi = round(user_data.weight / (height_m ** 2), 1)
    prompt = f"Expert Ayurvedic doctor. Profile: {user_data.dict()}, BMI: {bmi}. Respond STRICTLY with a JSON object."
    try:
        response = gemini_model.generate_content(prompt)
        raw_text = response.text.strip()
        if "{" in raw_text:
            raw_text = raw_text[raw_text.find("{"):raw_text.rfind("}")+1]
        return json.loads(raw_text)
    except:
        return {"dosha": "Vata-Kapha", "description": "Fallback profile generated."}

@app.get("/medicines")
def get_all_medicines():
    return {"products": list(inventory_collection.find({}, {"_id": 0}))}

# ==========================================
# AI DIAGNOSTIC ENDPOINT
# ==========================================
@app.post("/predict")
def predict_disease(data: UserInput):
    try:
        if not model: 
            return {"error": "Model not loaded"}

        force_skip = "skip_followup" in data.text.lower()
        clean_text = data.text.replace("skip_followup.", "").strip()

        valid_symptoms, detected_severity = extract_and_map_symptoms(clean_text)
        
        if not valid_symptoms:
            if data.is_final_check:
                return {"status": "error", "message": "Without any recognized symptoms, I cannot safely provide a diagnosis. Please try describing your condition using specific medical terms."}
            
            fallback_pool = ["headache", "high_fever", "stomach_pain", "fatigue", "nausea", "chills", "cough"]
            suggestions = [s for s in fallback_pool if s in symptoms_list]
            if len(suggestions) < 4 and len(symptoms_list) > 0:
                extra = [s for s in symptoms_list if s not in suggestions]
                suggestions.extend(extra[:4 - len(suggestions)])
                
            return {
                "status": "needs_more_info",
                "message": "I didn't quite catch any specific medical symptoms from your description. To help me diagnose you, are you experiencing any of these common issues?",
                "follow_up_symptoms": suggestions[:5],
                "extracted_symptoms": [],
                "current_top_prediction": "Unknown",
                "confidence": 0.0
            }

        # Phase 1: Fast-Track Clinical Interceptor
        top_disease = get_heuristic_diagnosis(valid_symptoms)
        feature_contributions = []
        
        if top_disease:
            print(f"INFO: High-confidence primary match established: {top_disease}")
            confidence = 0.98 
            
        else:
            # Phase 2: Probabilistic Ensemble Inference
            print("INFO: Initiating Deep-Feature Ensemble ML Analysis...")
            
            if hasattr(model, 'feature_names_in_'):
                expected_features = list(model.feature_names_in_)
            else:
                expected_features = symptoms_list

            input_dict = {sym: 0 for sym in expected_features}
            for symptom in valid_symptoms:
                if symptom in input_dict:
                    input_dict[symptom] = 1
                    
            input_df = pd.DataFrame([input_dict], columns=expected_features)
            raw_probabilities = model.predict_proba(input_df)[0]
            temp = 1.00 
            scaled_probs = np.exp(raw_probabilities / temp) / np.sum(np.exp(raw_probabilities / temp))
            
            if data.is_final_check:
                for idx, cls_label in enumerate(model.classes_):
                    decoded_name = le.inverse_transform([cls_label])[0]
                    if decoded_name in critical_diseases:
                        scaled_probs[idx] = 0.0 

            top_position = int(np.argmax(scaled_probs))
            actual_class_label = model.classes_[top_position]
            top_disease = le.inverse_transform([actual_class_label])[0]
            
            if data.is_final_check:
                confidence = scaled_probs[top_position] / (np.sum(scaled_probs) + 1e-9)
            else:
                confidence = scaled_probs[top_position]

            # XAI Feature Impact Calculation (SHAP)
            if xgb_base:
                try:
                    explainer = shap.TreeExplainer(xgb_base)
                    shap_values = explainer.shap_values(input_df)
                    impact_array = shap_values[top_position][0] if isinstance(shap_values, list) else shap_values[0]
                    for i, feature in enumerate(expected_features):
                        if input_df[feature].iloc[0] == 1:
                            feature_contributions.append({
                                "symptom": feature.replace('_', ' ').title(),
                                "impact_score": round(float(impact_array[i]), 4)
                            })
                    feature_contributions = sorted(feature_contributions, key=lambda x: x['impact_score'], reverse=True)
                except: pass

        # Phase 3: Clinical Safety & Doctor Clarification Routing
        if not data.is_final_check:
            if top_disease in critical_diseases and len(valid_symptoms) < 3:
                return {
                    "status": "needs_more_info",
                    "message": f"A {valid_symptoms[0].replace('_', ' ')} can be caused by many things. To ensure your safety, are you also feeling any dizziness, blurred vision, or sudden weakness?",
                    "extracted_symptoms": valid_symptoms,
                    "current_top_prediction": top_disease,
                    "confidence": round(float(confidence * 100), 2),
                    "follow_up_symptoms": ["dizziness", "blurred_vision", "unsteadiness", "stiff_neck"]
                }
            elif len(valid_symptoms) < 3:
                fallback_pool = ["headache", "fatigue", "nausea", "chills", "sweating", "stomach_pain", "cough"]
                suggestions = [s for s in fallback_pool if s in symptoms_list and s not in valid_symptoms]
                if len(suggestions) < 4 and len(symptoms_list) > 0:
                    extra = [s for s in symptoms_list if s not in valid_symptoms and s not in suggestions]
                    suggestions.extend(extra[:4 - len(suggestions)])
                symptom_str = ", ".join([s.replace("_", " ") for s in valid_symptoms])
                
                return {
                    "status": "needs_more_info",
                    "message": f"You mentioned {symptom_str}. That is a good start, but many conditions share these early signs. To help me narrow down the diagnosis, are you also feeling any of these?",
                    "follow_up_symptoms": suggestions[:4],
                    "extracted_symptoms": valid_symptoms,
                    "current_top_prediction": top_disease,
                    "confidence": round(float(confidence * 100), 2)
                }

        # Emergency Final Warning
        if top_disease in critical_diseases and confidence > 0.40:
            logs_collection.insert_one({"username": data.username, "symptoms": clean_text, "predicted_disease": top_disease, "status": "EMERGENCY", "timestamp": datetime.now()})
            return {
                "status": "CRITICAL",
                "diagnosis": top_disease,
                "confidence": round(float(confidence * 100), 2),
                "message": f"EMERGENCY: Symptoms indicate {top_disease}. Seek immediate hospital care."
            }

        logs_collection.insert_one({"username": data.username, "symptoms": clean_text, "predicted_disease": top_disease, "status": "COMPLETED", "timestamp": datetime.now()})

        # Phase 4: Treatment Ontology Mapping
        db_keys = list(ayurveda_db.keys())
        disease_data = {}
        if db_keys:
            best_match, score = process.extractOne(top_disease, db_keys)
            if score >= 70:
                disease_data = ayurveda_db[best_match]
                
        disease_medicines = []
        if isinstance(disease_data, dict):
            age_map = {"children": "child", "youth": "young", "elderly": "elder"}
            mapped_age = age_map.get(data.age_category.lower(), "young")
            mapped_gender = "female" if data.gender.lower() == "female" else "male"
            mapped_severity = data.severity.lower() if data.severity.lower() in ["low", "medium", "high"] else "medium"
            composite_key = f"{mapped_age}_{mapped_gender}_{mapped_severity}"
            disease_medicines = disease_data.get(composite_key, [])
            if not disease_medicines:
                for k, v in disease_data.items():
                    if isinstance(v, list) and len(v) > 0:
                        disease_medicines = v
                        break
        elif isinstance(disease_data, list):
            disease_medicines = disease_data
                
        if not disease_medicines:
            disease_medicines = [
                {"medicine_name": "Divya Ashwagandha Vati", "dosage": "1 tablet twice daily"},
                {"medicine_name": "Triphala Churna", "dosage": "1 teaspoon at bedtime"}
            ]
        
        # 🚀 EXTRACTING ACTUAL HERBS FROM THE JSON
        ayurveda_protocol_list = []
        user_age_cat = data.age_category.lower()
        user_severity = data.severity.lower()

        for med in disease_medicines:
            if isinstance(med, dict):
                base_dose = med.get("dosage", "Standard Dose")
                name = med.get("medicine_name", "Ayurvedic Protocol")
                
                # Fetch the array of real herbs from your medicine_master.json
                herbs = med.get("herb_sanskrit", [])
                
                # Clean up scraping artifacts like "6 nights" or "9 times"
                if isinstance(herbs, list) and len(herbs) > 0:
                    clean_herbs = [
                        str(h).title() for h in herbs 
                        if not any(char.isdigit() for char in str(h)) 
                        and "days" not in str(h).lower() 
                        and "times" not in str(h).lower()
                        and len(str(h)) > 2
                    ]
                    
                    # If clean herbs exist, overwrite the generic "Protocol" name with the real medicines
                    if clean_herbs:
                        if "Protocol" in name or name == "Ayurvedic Herb":
                            name = ", ".join(clean_herbs[:5])  # e.g., "Amalaki, Bibhitaki, Bilva"
                        else:
                            name = f"{name} ({', '.join(clean_herbs[:3])})"
            else:
                base_dose = "Standard Dose"
                name = str(med)

            if user_age_cat in ["children", "elderly", "child", "elder"]:
                if "Half Dose" not in base_dose:
                    base_dose = f"Pediatric/Geriatric Scale (Half Dose): {base_dose}"
            
            if user_severity == "high":
                if "INTENSIVE" not in base_dose:
                    base_dose = f"INTENSIVE: {base_dose} (Requires Physician Monitoring)"

            ayurveda_protocol_list.append({
                "medicine_name": name,
                "dosage": base_dose
            })

        mapped_gender = "female" if data.gender.lower() == "female" else "male"
        if mapped_gender == "male": 
            preg_warning = ["Not applicable for male patients."]
        elif data.is_pregnant: 
            preg_warning = ["Contraindicated during pregnancy. Consult a physician immediately."]
        else: 
            preg_warning = ["Safe for general use."]

        return {
            "status": "success",
            "diagnosis": top_disease,
            "confidence": round(float(confidence * 100), 2),
            "extracted_symptoms": valid_symptoms,
            "detected_severity": data.severity,
            "prescription": {"pregnancy_status": preg_warning},
            "ayurveda_protocol": ayurveda_protocol_list, 
            "shap_explainability": feature_contributions 
        }
    
    except Exception as e:
        import traceback
        print("\n❌ CRITICAL BACKEND CRASH DETECTED ❌")
        traceback.print_exc() 
        return {"status": "error", "message": f"Backend Error: {str(e)}"}

# ==========================================
# AUTHENTICATION & USER MANAGEMENT
# ==========================================
@app.post("/register")
def register_user(user: UserRegister):
    if users_collection.find_one({"name": user.name}): raise HTTPException(status_code=400, detail="Username already exists")
    hashed_password = bcrypt.hashpw(user.password.encode('utf-8'), bcrypt.gensalt())
    dosha_info = generate_ayurvedic_profile(user)
    users_collection.insert_one({**user.dict(), "password": hashed_password.decode('utf-8'), "ayurvedic_profile": dosha_info})
    return {"message": "User registered successfully!", "profile": dosha_info}

@app.post("/login")
def login_user(user: UserLogin):
    db_user = users_collection.find_one({"name": user.name})
    if not db_user or not bcrypt.checkpw(user.password.encode('utf-8'), db_user["password"].encode('utf-8')):
        raise HTTPException(status_code=400, detail="Invalid username or password")
    return {"message": "Login successful", "user": {"name": db_user.get("name"), "ayurvedic_profile": db_user.get("ayurvedic_profile")}}

# ==========================================
# E-COMMERCE & FINANCIAL TRANSACTIONS
# ==========================================
try:
    razorpay_client = razorpay.Client(auth=(os.getenv("RAZORPAY_KEY_ID"), os.getenv("RAZORPAY_KEY_SECRET")))
except:
    razorpay_client = None

class OrderRequest(BaseModel):
    amount: int; currency: str = "INR"

class PaymentVerification(BaseModel):
    razorpay_order_id: str; razorpay_payment_id: str; razorpay_signature: str; cart_items: list; username: str; total_amount: int

@app.post("/create-order")
def create_order(order: OrderRequest):
    return {"order_id": razorpay_client.order.create({"amount": order.amount * 100, "currency": order.currency, "receipt": "receipt_" + str(datetime.now().timestamp())})["id"]}

@app.post("/verify-payment")
def verify_payment(data: PaymentVerification):
    try:
        razorpay_client.utility.verify_payment_signature({'razorpay_order_id': data.razorpay_order_id, 'razorpay_payment_id': data.razorpay_payment_id, 'razorpay_signature': data.razorpay_signature})
        orders_collection.insert_one({"username": data.username, "order_id": data.razorpay_order_id, "amount_paid": data.total_amount, "status": "Paid", "timestamp": datetime.now()})
        return {"status": "success"}
    except: raise HTTPException(status_code=400, detail="Invalid Signature")

@app.get("/admin/orders")
def get_all_orders():
    return {"orders": [{**o, "timestamp": o["timestamp"].strftime("%Y-%m-%d %H:%M") if isinstance(o.get("timestamp"), datetime) else o.get("timestamp")} for o in list(orders_collection.find({}, {"_id": 0}).sort("timestamp", -1))]}

@app.get("/admin/logs")
def get_all_logs():
    return {"logs": [{**l, "timestamp": l["timestamp"].strftime("%Y-%m-%d %H:%M") if isinstance(l.get("timestamp"), datetime) else l.get("timestamp")} for l in list(logs_collection.find({}, {"_id": 0}).sort("timestamp", -1))]}