from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import pickle
import os
import json
from datetime import datetime
from app.symptom_nlp import extract_symptoms_from_text

from pymongo import MongoClient
import bcrypt  
from dotenv import load_dotenv
from fastapi import HTTPException
from google import genai
from google.genai import types

import razorpay

load_dotenv() 

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class UserInput(BaseModel):
    text: str
    username: str

class UserRegister(BaseModel):
    name: str
    password: str
    age: int
    gender: str
    weight: float
    height: float
    digestion: str
    sleep: str
    weather: str
    frame: str

class UserLogin(BaseModel):
    name: str
    password: str

# --- DATABASE SETUP ---
MONGO_URI = os.getenv("MONGO_URI")
try:
    client = MongoClient(MONGO_URI)
    db = client["diagnosis_system"] 
    users_collection = db["users"]   
    logs_collection = db["diagnostic_logs"] 
    orders_collection = db["orders"]        
    inventory_collection = db["pharmacy_products_final"] # Our newly seeded collection!
    print("✅ Connected to MongoDB Atlas")
except Exception as e:
    print(f"❌ MongoDB Connection Error: {e}")

current_dir = os.path.dirname(os.path.abspath(__file__))
model_path = os.path.join(current_dir, "../models/disease_model.pkl")
encoder_path = os.path.join(current_dir, "../models/label_encoder.pkl")
kb_path = os.path.join(current_dir, "../data/ayurveda_kb_final.json")

try:
    with open(model_path, "rb") as f: model = pickle.load(f)
    with open(encoder_path, "rb") as f: le = pickle.load(f)
    print("✅ ML Model Loaded")
except Exception as e: model = None

try:
    with open(kb_path, "r", encoding="utf-8") as f: ayurveda_db = json.load(f)
    print("✅ Ayurveda DB Loaded")
except Exception as e: ayurveda_db = {}

gemini_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# ==========================================================
# 🛒 ZERO-LATENCY STORE ENDPOINT
# ==========================================================
@app.get("/medicines")
def get_all_medicines():
    """Fetches the pre-built AI store catalog from MongoDB instantly."""
    products = list(inventory_collection.find({}, {"_id": 0}))
    return {"products": products}

# ==========================================================
# 🌿 GENERATIVE AI DOSHA ENGINE
# ==========================================================
def generate_ayurvedic_profile(user_data: UserRegister):
    height_m = user_data.height / 100.0
    bmi = round(user_data.weight / (height_m ** 2), 1)
    
    prompt = f"""
    Act as an expert Ayurvedic doctor. Analyze this patient:
    Age: {user_data.age}, Gender: {user_data.gender}, BMI: {bmi}, 
    Body Frame: {user_data.frame}, Digestion: {user_data.digestion}, 
    Sleep: {user_data.sleep}, Weather: {user_data.weather}.
    
    Task 1: Determine their primary Ayurvedic Dosha.
    Task 2: Build a practical, daily Ayurvedic Lifestyle Plan.
    
    CRITICAL INSTRUCTION: For arrays (diet_do, diet_dont, yoga), PROVIDE EXACTLY 3 BULLET POINTS UNDER 10 WORDS. NO LONG SENTENCES.
    
    Return EXACTLY JSON format:
    {{
        "dosha": "Name of Dosha",
        "description": "A highly detailed, engaging 3-sentence paragraph explaining their body type.",
        "diet_do": ["Short item 1", "Short item 2", "Short item 3"],
        "diet_dont": ["Short item 1", "Short item 2", "Short item 3"],
        "yoga": ["Specific yoga pose 1", "Specific yoga pose 2", "Specific yoga pose 3"]
    }}
    """
    try:
        response = gemini_client.models.generate_content(
            model='gemini-2.5-flash', contents=prompt,
            config=types.GenerateContentConfig(response_mime_type="application/json")
        )
        return json.loads(response.text)
    except Exception as e:
        return {"dosha": "Analysis Failed", "description": "System Offline.", "diet_do": [], "diet_dont": [], "yoga": []}

# ==========================================================
# 🩺 ML DISEASE PREDICTION ENDPOINT
# ==========================================================
@app.post("/predict")
def predict_disease(data: UserInput):
    if not model: return {"error": "Model not loaded"}

    input_vector, detected_symptoms, metadata = extract_symptoms_from_text(data.text)
    
    if len(detected_symptoms) < 2:
        reason = "I couldn't detect any specific medical symptoms in your text." if len(detected_symptoms) == 0 else f"You only mentioned '{detected_symptoms[0].replace('_', ' ')}'. A single symptom is too broad for an accurate diagnosis."
        logs_collection.insert_one({"username": data.username, "symptoms": data.text, "predicted_disease": "Blocked by Guardrail", "confidence": 0, "timestamp": datetime.now()})
        return {"disease": "Unknown", "confidence": 0, "detected_symptoms": detected_symptoms, "metadata": metadata, "alternative_predictions": [], "follow_up": f"{reason} Please describe your condition in more detail.", "ayurveda": {}}

    probabilities = model.predict_proba([input_vector])[0]
    predictions = [{"disease": le.inverse_transform([idx])[0].strip(), "confidence": prob * 100} for idx, prob in enumerate(probabilities) if prob > 0]
            
    for p in predictions:
        disease = p["disease"]
        if "yellowish_skin" in detected_symptoms and "yellowing_of_eyes" in detected_symptoms:
            if disease == "Jaundice" and "itching" not in detected_symptoms: p["confidence"] += 50.0  
            elif disease == "Chronic cholestasis" and "itching" in detected_symptoms: p["confidence"] += 50.0 
        if "joint_pain" in detected_symptoms and "skin_rash" in detected_symptoms:
            if disease == "Dengue": p["confidence"] += 30.0

    predictions = sorted(predictions, key=lambda x: x["confidence"], reverse=True)[:3]
    total_conf = sum(p["confidence"] for p in predictions)
    if total_conf > 0:
        for p in predictions: p["confidence"] = round((p["confidence"] / total_conf) * 100, 1)

    top_disease, top_confidence = predictions[0]["disease"], predictions[0]["confidence"]
    follow_up = f"Confidence is split. It is most likely {top_disease} ({top_confidence}%), but symptoms also align with {predictions[1]['disease']} ({predictions[1]['confidence']}%)." if top_confidence < 80.0 and len(predictions) > 1 else None

    ayurveda_info = ayurveda_db.get(top_disease)
    if not ayurveda_info:
        for key, kb_data in ayurveda_db.items():
            if top_disease.lower() in key.lower() or key.lower() in top_disease.lower():
                ayurveda_info = kb_data
                break
    if not ayurveda_info: ayurveda_info = {"medicine_names": [], "precautions": ["No specific Ayurvedic data found."], "source": "System"}

    logs_collection.insert_one({"username": data.username, "symptoms": data.text, "predicted_disease": top_disease, "confidence": top_confidence, "timestamp": datetime.now()})

    return {"disease": top_disease, "confidence": top_confidence, "alternative_predictions": predictions[1:], "follow_up": follow_up, "detected_symptoms": detected_symptoms, "metadata": metadata, "ayurveda": ayurveda_info}

# ==========================================================
# 🔒 AUTHENTICATION ENDPOINTS
# ==========================================================
@app.post("/register")
def register_user(user: UserRegister):
    if users_collection.find_one({"name": user.name}): raise HTTPException(status_code=400, detail="Username already exists")
    hashed_password = bcrypt.hashpw(user.password.encode('utf-8'), bcrypt.gensalt())
    dosha_info = generate_ayurvedic_profile(user)
    users_collection.insert_one({
        "name": user.name, "password": hashed_password.decode('utf-8'), "age": user.age, "gender": user.gender,
        "weight": user.weight, "height": user.height, "digestion": getattr(user, 'digestion', 'Balanced'),
        "sleep": getattr(user, 'sleep', 'Moderate'), "weather": getattr(user, 'weather', 'Tolerant'),
        "frame": getattr(user, 'frame', 'Medium'), "ayurvedic_profile": dosha_info  
    })
    return {"message": "User registered successfully!", "profile": dosha_info}

@app.post("/login")
def login_user(user: UserLogin):
    db_user = users_collection.find_one({"name": user.name})
    if not db_user or not bcrypt.checkpw(user.password.encode('utf-8'), db_user["password"].encode('utf-8')):
        raise HTTPException(status_code=400, detail="Invalid username or password")
    return {"message": "Login successful", "user": {"name": db_user.get("name"), "age": db_user.get("age"), "gender": db_user.get("gender"), "weight": db_user.get("weight"), "height": db_user.get("height"), "ayurvedic_profile": db_user.get("ayurvedic_profile")}}




# ==========================================================
# 💳 REAL RAZORPAY PAYMENT GATEWAY ENDPOINTS
# ==========================================================
razorpay_client = razorpay.Client(auth=(os.getenv("RAZORPAY_KEY_ID"), os.getenv("RAZORPAY_KEY_SECRET")))

class OrderRequest(BaseModel):
    amount: int
    currency: str = "INR"

class PaymentVerification(BaseModel):
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str
    cart_items: list
    username: str
    total_amount: int

@app.post("/create-order")
def create_order(order: OrderRequest):
    """Generates a secure order ID from Razorpay"""
    try:
        data = {
            "amount": order.amount * 100, # Razorpay expects paise
            "currency": order.currency,
            "receipt": "receipt_" + str(datetime.now().timestamp())
        }
        payment_order = razorpay_client.order.create(data=data)
        return {"order_id": payment_order["id"], "amount": payment_order["amount"]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/verify-payment")
def verify_payment(data: PaymentVerification):
    """Verifies the transaction signature and saves the order to MongoDB"""
    try:
        params_dict = {
            'razorpay_order_id': data.razorpay_order_id,
            'razorpay_payment_id': data.razorpay_payment_id,
            'razorpay_signature': data.razorpay_signature
        }
        razorpay_client.utility.verify_payment_signature(params_dict)
        
        order_record = {
            "username": data.username,
            "order_id": data.razorpay_order_id,
            "payment_id": data.razorpay_payment_id,
            "amount_paid": data.total_amount,
            "items": data.cart_items,
            "status": "Paid & Processing",
            "timestamp": datetime.now()
        }
        orders_collection.insert_one(order_record)
        return {"status": "success", "message": "Payment verified and order placed!"}
    except razorpay.errors.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid Payment Signature")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==========================================================
# 👑 ADMIN PANEL ENDPOINTS
# ==========================================================
@app.get("/admin/orders")
def get_all_orders():
    """Fetches all successful payments/orders for the Admin."""
    orders = list(orders_collection.find({}, {"_id": 0}).sort("timestamp", -1))
    # Clean up dates for JSON serialization
    for order in orders:
        if "timestamp" in order and isinstance(order["timestamp"], datetime):
            order["timestamp"] = order["timestamp"].strftime("%Y-%m-%d %H:%M")
    return {"orders": orders}

@app.get("/admin/logs")
def get_all_logs():
    """Fetches all AI Diagnosis interactions for the Admin."""
    logs = list(logs_collection.find({}, {"_id": 0}).sort("timestamp", -1))
    for log in logs:
        if "timestamp" in log and isinstance(log["timestamp"], datetime):
            log["timestamp"] = log["timestamp"].strftime("%Y-%m-%d %H:%M")
    return {"logs": logs}