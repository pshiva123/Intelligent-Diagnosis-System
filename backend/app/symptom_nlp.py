import pickle
import os
import spacy
from spacy.matcher import PhraseMatcher
import re

# --- 1. LOAD SPACY NLP MODEL ---
print("🧠 Loading spaCy NLP Model for Symptom Extraction...")
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    print("Downloading spaCy model...")
    import subprocess
    subprocess.run(["python", "-m", "spacy", "download", "en_core_web_sm"])
    nlp = spacy.load("en_core_web_sm")

# --- 2. LOAD KAGGLE FEATURES ---
current_dir = os.path.dirname(os.path.abspath(__file__))
features_path = os.path.join(current_dir, "../models/symptom_features.pkl")

try:
    with open(features_path, "rb") as f:
        VALID_SYMPTOMS = pickle.load(f)
except FileNotFoundError:
    print("❌ Error: Models not found. Run train_model.py first.")
    VALID_SYMPTOMS = []

# --- 3. MEDICAL ONTOLOGY ---

# EXACT PHRASES (Matches exact word combinations)
SYMPTOM_MAP = {
    "headache": ["headache"],
    "head ache": ["headache"],
    "fever": ["high_fever"],
    "throw up": ["vomiting"],
    "nausea": ["nausea"],
    "itch": ["itching"],
    "rash": ["skin_rash"],
    "shiver": ["shivering"],
    "chill": ["chills"],
    "sweat": ["sweating"],
    "stomach ache": ["stomach_pain"],
    "stomach pain": ["stomach_pain"],
    "acidity": ["acidity"],
    "heartburn": ["acidity"],
    "chest pain": ["chest_pain"],
    "joint pain": ["joint_pain"],
    "neck pain": ["neck_pain"],
    "fatigue": ["fatigue"],
    "tired": ["fatigue"],
    "weakness": ["weakness_in_limbs"],
    "runny nose": ["runny_nose"],
    "sneeze": ["continuous_sneezing"],
    "cough": ["cough"],
    "breathless": ["breathlessness"],
    "weight loss": ["weight_loss"],
    "dizzy": ["dizziness"],
    "dizziness": ["dizziness"],
    "diarrhea": ["diarrhoea"],
    "fatigued": ["fatigue"],
    "body pain": ["muscle_pain", "joint_pain"],
    "body pains": ["muscle_pain", "joint_pain"]
}

# STRONG KEYWORDS (Single words that strongly indicate a symptom)
STRONG_KEYWORDS = {
    "yellow": ["yellowish_skin", "yellowing_of_eyes"],
    "puke": ["vomiting"],
    "vomit": ["vomiting"],
    "pimple": ["scurring", "skin_rash"],
    "acne": ["scurring", "skin_rash"],
    "sore": ["red_sore_around_nose"],
    "paralyze": ["weakness_of_one_body_side"],
    "body pain": ["muscle_pain", "joint_pain"],
    "body pains": ["muscle_pain", "joint_pain"],
    "fatigued": ["fatigue"],
    "fatigue": ["fatigue"]
}

# FLEXIBLE INTERSECTION (Matches if BOTH words appear anywhere in the text)
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
}

matcher = PhraseMatcher(nlp.vocab, attr="LEMMA")
for phrase, features in SYMPTOM_MAP.items():
    pattern = nlp(phrase)
    matcher.add(phrase, [pattern])

def extract_metadata(text):
    """Extracts the severity and duration of the symptoms."""
    doc = nlp(text.lower())
    severity = "Moderate"
    duration = "Recent"

    # 1. Severity extraction
    high_sev = ["severe", "terrible", "blinding", "unbearable", "extreme", "bad", "worst", "killing", "intense"]
    low_sev = ["mild", "slight", "little", "minor", "bearable"]

    for token in doc:
        if token.text in high_sev:
            severity = "High"
        elif token.text in low_sev:
            severity = "Low"

    # 2. Duration extraction (Regex for timeframes)
    duration_match = re.search(r'\b(\d+\s*(days|weeks|months|years)|since\s*\w+|for\s*\d+\s*\w+)\b', text.lower())
    if duration_match:
        duration = duration_match.group(0).title()

    return {"severity": severity, "duration": duration}

def extract_symptoms_from_text(user_input):
    doc = nlp(user_input.lower())
    extracted_symptoms = set()

    # METHOD 1: Phrase Matcher
    matches = matcher(doc)
    for match_id, start, end in matches:
        phrase = nlp.vocab.strings[match_id]
        if phrase in SYMPTOM_MAP:
            extracted_symptoms.update(SYMPTOM_MAP[phrase])

    user_lemmas = [token.lemma_ for token in doc if not token.is_stop and token.is_alpha]
    user_lemma_text = " ".join(user_lemmas)
    raw_text = user_input.lower()

    # METHOD 2: Strong Keywords
    for word, features in STRONG_KEYWORDS.items():
        if word in user_lemma_text or word in raw_text:
            extracted_symptoms.update(features)

    # METHOD 3: Flexible Intersection
    for (word1, word2), feature in FLEXIBLE_MATCHES.items():
        if (word1 in user_lemma_text or word1 in raw_text) and (word2 in user_lemma_text or word2 in raw_text):
            extracted_symptoms.add(feature)

    # Extract Metadata
    metadata = extract_metadata(user_input)

    input_vector = [0] * len(VALID_SYMPTOMS)
    matched_list = []
    
    for i, symptom in enumerate(VALID_SYMPTOMS):
        if symptom in extracted_symptoms:
            input_vector[i] = 1
            matched_list.append(symptom)
            
    return input_vector, matched_list, metadata