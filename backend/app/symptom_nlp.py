import joblib
import os
import spacy
from spacy.matcher import PhraseMatcher
import re
from thefuzz import process, fuzz

print("INFO: Loading spaCy NLP model for symptom extraction...")
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    print("Downloading spaCy model...")
    import subprocess
    subprocess.run(["python", "-m", "spacy", "download", "en_core_web_sm"])
    nlp = spacy.load("en_core_web_sm")

try:
    # Ensure this path matches where your ensemble saves the list
    current_dir = os.path.dirname(os.path.abspath(__file__))
    VALID_SYMPTOMS = joblib.load(os.path.join(current_dir, '../models/symptoms_list.pkl'))
except FileNotFoundError:
    try:
        # Fallback path just in case it runs from root
        VALID_SYMPTOMS = joblib.load('models/symptoms_list.pkl')
    except:
        print("ERROR: models/symptoms_list.pkl not found. Run train_ensemble.py first.")
        VALID_SYMPTOMS = []

# ==========================================
# 🚀 MASSIVELY EXPANDED SYMPTOM DICTIONARY
# ==========================================
SYMPTOM_MAP = {
    "headache": ["headache"], "head ache": ["headache"], "migraine": ["headache"],
    "dizzy": ["dizziness"], "dizziness": ["dizziness"], "lightheaded": ["dizziness"], "spinning": ["spinning_movements"],
    "lose balance": ["loss_of_balance"], "fainting": ["loss_of_balance"],
    "fever": ["high_fever"], "temperature": ["high_fever"], "hot": ["high_fever"], "mild fever": ["mild_fever"],
    "shiver": ["shivering"], "shivering": ["shivering"], 
    "chill": ["chills"], "chills": ["chills"], 
    "cold": ["chills", "continuous_sneezing", "runny_nose", "congestion"],
    "sweat": ["sweating"], "sweating": ["sweating"],
    "stomach ache": ["stomach_pain"], "stomach pain": ["stomach_pain"], "tummy ache": ["stomach_pain"], "belly ache": ["belly_pain"],
    "throw up": ["vomiting"], "puke": ["vomiting"], "vomiting": ["vomiting"],
    "nausea": ["nausea"], "feel sick": ["nausea"],
    "acidity": ["acidity"], "heartburn": ["acidity"], "gas": ["passage_of_gases"],
    "indigestion": ["indigestion"], "upset stomach": ["indigestion", "nausea"],
    "diarrhea": ["diarrhoea"], "loose motion": ["diarrhoea"], "constipation": ["constipation"],
    "appetite loss": ["loss_of_appetite"], "not hungry": ["loss_of_appetite"], "excessive hunger": ["excessive_hunger"],
    "cough": ["cough"], "coughing": ["cough"],
    "runny nose": ["runny_nose"], "sneeze": ["continuous_sneezing"], "sneezing": ["continuous_sneezing"],
    "breathless": ["breathlessness"], "short of breath": ["breathlessness"], "can't breathe": ["breathlessness"], "wheezing": ["breathlessness"],
    "chest pain": ["chest_pain"], "heavy chest": ["chest_pain"], "phlegm": ["phlegm"],
    "sore throat": ["throat_irritation"], "throat pain": ["throat_irritation"],
    "fatigue": ["fatigue"], "tired": ["fatigue"], "exhausted": ["fatigue"], "no energy": ["lethargy"], "lethargy": ["lethargy"],
    "weakness": ["weakness_in_limbs"], "weak": ["weakness_in_limbs"],
    "muscle pain": ["muscle_pain"], "body ache": ["muscle_pain"], "body pain": ["muscle_pain", "joint_pain"],
    "joint pain": ["joint_pain"], "neck pain": ["neck_pain"], "back pain": ["back_pain"], "knee pain": ["knee_pain"],
    "stiff neck": ["stiff_neck"], "cramps": ["cramps"],
    "itch": ["itching"], "scratching": ["itching"],
    "rash": ["skin_rash"], "hives": ["skin_rash"], "red spots": ["red_spots_over_body"],
    "pimples": ["pus_filled_pimples", "scurring"], "acne": ["pus_filled_pimples", "scurring"],
    "weight loss": ["weight_loss"], "losing weight": ["weight_loss"],
    "weight gain": ["weight_gain"], "gaining weight": ["weight_gain"],
    "bruise": ["bruising"], "swelling": ["swelling_joints"],
    "yellow skin": ["yellowish_skin"],
    "blurry vision": ["blurred_and_distorted_vision"], "can't see": ["blurred_and_distorted_vision"],
    "red eye": ["redness_of_eyes"], "eye pain": ["pain_behind_the_eyes"], "yellow eyes": ["yellowing_of_eyes"],
    "loss of smell": ["loss_of_smell"], "can't smell": ["loss_of_smell"],
    "burn urine": ["burning_micturition"], "pain peeing": ["burning_micturition"],
    "frequent pee": ["continuous_feel_of_urine"], "dark urine": ["dark_urine"], "yellow urine": ["dark_urine"]
}

STRONG_KEYWORDS = {
    "yellow": ["yellowish_skin", "yellowing_of_eyes"],
    "puke": ["vomiting"],
    "vomit": ["vomiting"],
    "pimple": ["scurring", "skin_rash"],
    "acne": ["scurring", "skin_rash"],
    "sore": ["red_sore_around_nose"],
    "paralyze": ["weakness_of_one_body_side"],
    "fatigue": ["fatigue"],
    "exhausted": ["fatigue", "lethargy"],
    "blood": ["bloody_stool", "blood_in_sputum"]
}

FLEXIBLE_MATCHES = {
    ("skin", "yellow"): "yellowish_skin",
    ("eye", "yellow"): "yellowing_of_eyes",
    ("stomach", "pain"): "stomach_pain",
    ("stomach", "hurt"): "stomach_pain",
    ("abdomen", "pain"): "abdominal_pain",
    ("chest", "pain"): "chest_pain",
    ("neck", "pain"): "neck_pain",
    ("neck", "stiff"): "stiff_neck",
    ("joint", "pain"): "joint_pain",
    ("muscle", "pain"): "muscle_pain",
    ("body", "ache"): "muscle_pain",
    ("body", "pain"): "muscle_pain",
    ("vision", "blur"): "blurred_and_distorted_vision",
    ("eye", "blur"): "blurred_and_distorted_vision",
    ("burn", "urine"): "burning_micturition",
    ("burn", "pee"): "burning_micturition",
    ("frequent", "urinate"): "continuous_feel_of_urine",
    ("lot", "pee"): "continuous_feel_of_urine",
    ("lost", "weight"): "weight_loss",
    ("gain", "weight"): "weight_gain",
    ("short", "breath"): "breathlessness",
    ("sore", "throat"): "throat_irritation",
}

DIRECT_CONDITION_MAP = {
    "fungal infection": ["itching", "skin_rash", "dischromic_patches"],
    "migraine": ["headache", "blurred_and_distorted_vision", "stiff_neck", "visual_disturbances"],
    "jaundice": ["yellowish_skin", "yellowing_of_eyes", "dark_urine", "abdominal_pain"],
    "gerd": ["stomach_pain", "acidity", "chest_pain", "cough"],
    "arthritis": ["joint_pain", "swelling_joints", "movement_stiffness"],
    "allergy": ["continuous_sneezing", "shivering", "watering_from_eyes", "chills"],
    "diabetes": ["polyuria", "increased_appetite", "excessive_hunger", "weight_loss", "lethargy"],
    "malaria": ["chills", "high_fever", "sweating", "headache", "muscle_pain", "nausea"],
    "typhoid": ["chills", "high_fever", "headache", "nausea", "abdominal_pain", "diarrhoea"],
    "dengue": ["skin_rash", "joint_pain", "high_fever", "pain_behind_the_eyes", "muscle_pain", "red_spots_over_body"],
    "chicken pox": ["itching", "skin_rash", "high_fever", "red_spots_over_body", "lethargy"],
    "pneumonia": ["chills", "cough", "high_fever", "breathlessness", "chest_pain", "fast_heart_rate"],
    "common cold": ["continuous_sneezing", "chills", "cough", "high_fever", "runny_nose", "congestion"]
}

matcher = PhraseMatcher(nlp.vocab, attr="LEMMA")
for phrase, features in SYMPTOM_MAP.items():
    pattern = nlp(phrase)
    matcher.add(phrase, [pattern])

def extract_severity(text):
    doc = nlp(text.lower())
    severity = "medium" 
    high_sev = ["severe", "terrible", "blinding", "unbearable", "extreme", "bad", "worst", "killing", "intense"]
    low_sev = ["mild", "slight", "little", "minor", "bearable"]
    for token in doc:
        if token.text in high_sev:
            severity = "high"
        elif token.text in low_sev:
            severity = "low"
    return severity

def extract_and_map_symptoms(user_input: str):
    doc = nlp(user_input.lower())
    extracted_symptoms = set()

    matches = matcher(doc)
    for match_id, start, end in matches:
        phrase = nlp.vocab.strings[match_id]
        if phrase in SYMPTOM_MAP:
            extracted_symptoms.update(SYMPTOM_MAP[phrase])

    user_lemmas = [token.lemma_ for token in doc if not token.is_stop and token.is_alpha]
    user_lemma_text = " ".join(user_lemmas)
    raw_text = user_input.lower()

    for word, features in STRONG_KEYWORDS.items():
        if word in user_lemma_text or word in raw_text:
            extracted_symptoms.update(features)

    for (word1, word2), feature in FLEXIBLE_MATCHES.items():
        if (word1 in user_lemma_text or word1 in raw_text) and (word2 in user_lemma_text or word2 in raw_text):
            extracted_symptoms.add(feature)

    clean_words = raw_text.replace('.', '').replace(',', '').split()
    for condition, features in DIRECT_CONDITION_MAP.items():
        if condition in raw_text:
            extracted_symptoms.update(features)
            continue
        for word in clean_words:
            if len(word) >= 4 and len(condition) >= 4:
                if fuzz.ratio(condition, word) >= 85:
                    extracted_symptoms.update(features)
                    break

    for valid_sym in VALID_SYMPTOMS:
        clean_sym = valid_sym.replace("_", " ")
        if clean_sym in raw_text or valid_sym in raw_text:
            extracted_symptoms.add(valid_sym)
            
    # 🚀 DYNAMIC FUZZY MATCHING FOR CUSTOM DATASETS (Fixes typos like "legpains")
    if not extracted_symptoms:
        clean_list = [v.replace("_", " ") for v in VALID_SYMPTOMS]
        for word in clean_words:
            if len(word) >= 5: 
                best_match, score = process.extractOne(word, VALID_SYMPTOMS)
                clean_match, clean_score = process.extractOne(word, clean_list)
                
                if score >= 85:
                    extracted_symptoms.add(best_match)
                elif clean_score >= 85:
                    idx = clean_list.index(clean_match)
                    extracted_symptoms.add(VALID_SYMPTOMS[idx])

    final_valid_symptoms = [sym for sym in extracted_symptoms if sym in VALID_SYMPTOMS]
    detected_severity = extract_severity(user_input)
            
    return final_valid_symptoms, detected_severity