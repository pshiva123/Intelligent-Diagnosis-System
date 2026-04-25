# clinical_rules.py

# This is our Heuristic Rules Engine. 
# It maps common, everyday symptom combinations to safe, accurate diseases.
# Use sets {} so the order of symptoms doesn't matter!

COMMON_CASES = [
    # ==========================================
    # 1. FEVERS & SYSTEMIC INFECTIONS
    # ==========================================
    ({"headache", "high_fever"}, "Common Cold"),
    ({"headache", "mild_fever"}, "Common Cold"),
    ({"high_fever", "headache", "chills", "sweating"}, "Malaria"),
    ({"high_fever", "chills", "vomiting", "headache"}, "Malaria"),
    ({"high_fever", "headache", "muscle_pain", "joint_pain"}, "Dengue"),
    ({"high_fever", "pain_behind_the_eyes", "joint_pain", "skin_rash"}, "Dengue"),
    ({"high_fever", "headache", "abdominal_pain", "chills"}, "Typhoid"),
    ({"high_fever", "nausea", "constipation", "headache"}, "Typhoid"),
    ({"mild_fever", "itching", "skin_rash", "fatigue"}, "Chicken pox"),
    ({"mild_fever", "red_spots_over_body", "lethargy"}, "Chicken pox"),

    # ==========================================
    # 2. LIVER & HEPATIC (Kamala)
    # ==========================================
    ({"high_fever", "headache", "yellowish_skin", "nausea"}, "Jaundice"),
    ({"yellowing_of_eyes", "yellowish_skin", "fatigue"}, "Jaundice"),
    ({"dark_urine", "yellowish_skin", "vomiting", "loss_of_appetite"}, "Jaundice"),
    ({"yellowish_skin", "nausea", "loss_of_appetite", "abdominal_pain"}, "hepatitis A"),
    ({"yellowing_of_eyes", "lethargy", "fatigue", "dark_urine"}, "Hepatitis B"),

    # ==========================================
    # 3. RESPIRATORY & ENT
    # ==========================================
    ({"continuous_sneezing", "chills", "runny_nose"}, "Allergy"),
    ({"continuous_sneezing", "watering_from_eyes", "congestion"}, "Allergy"),
    ({"cough", "high_fever", "breathlessness"}, "Bronchial Asthma"),
    ({"cough", "breathlessness", "mucoid_sputum"}, "Bronchial Asthma"),
    ({"chills", "high_fever", "breathlessness", "chest_pain", "cough"}, "Pneumonia"),
    ({"high_fever", "cough", "phlegm", "chest_pain"}, "Pneumonia"),

    # ==========================================
    # 4. GASTROINTESTINAL & STOMACH
    # ==========================================
    ({"acidity", "indigestion", "stomach_pain"}, "GERD"),
    ({"acidity", "ulcers_on_tongue", "vomiting"}, "GERD"),
    ({"vomiting", "diarrhoea", "abdominal_pain"}, "Gastroenteritis"),
    ({"stomach_pain", "acidity", "vomiting", "loss_of_appetite"}, "Peptic ulcer diseae"),
    ({"constipation", "pain_during_bowel_movements", "pain_in_anal_region"}, "Dimorphic hemmorhoids(piles)"),
    ({"bloody_stool", "pain_in_anal_region", "irritation_in_anus"}, "Dimorphic hemmorhoids(piles)"),

    # ==========================================
    # 5. SKIN & DERMATOLOGICAL
    # ==========================================
    ({"skin_rash", "nodal_skin_eruptions", "itching"}, "Fungal infection"),
    ({"itching", "skin_rash", "dischromic _patches"}, "Fungal infection"),
    ({"pus_filled_pimples", "blackheads", "scurring"}, "Acne"),
    ({"skin_rash", "pus_filled_pimples"}, "Acne"),
    ({"skin_peeling", "silver_like_dusting", "itching"}, "Psoriasis"),
    ({"blister", "red_sore_around_nose", "yellow_crust_ooze"}, "Impetigo"),

    # ==========================================
    # 6. NEUROLOGICAL & PAIN
    # ==========================================
    ({"headache"}, "Migraine"), # The ultimate bug-fix anchor
    ({"headache", "visual_disturbances", "acidity"}, "Migraine"),
    ({"headache", "blurred_and_distorted_vision", "depression"}, "Migraine"),
    ({"spinning_movements", "loss_of_balance", "headache"}, "(vertigo) Paroymsal  Positional Vertigo"),
    ({"spinning_movements", "nausea", "loss_of_balance"}, "(vertigo) Paroymsal  Positional Vertigo"),
    ({"neck_pain", "dizziness", "weakness_in_limbs"}, "Cervical spondylosis"),
    ({"back_pain", "neck_pain", "loss_of_balance"}, "Cervical spondylosis"),

    # ==========================================
    # 7. CHRONIC & LIFESTYLE CONDITIONS
    # ==========================================
    ({"excessive_hunger", "polyuria", "increased_appetite", "weight_loss"}, "Diabetes "),
    ({"fatigue", "weight_loss", "restlessness", "sweating"}, "Hyperthyroidism"),
    ({"fatigue", "weight_gain", "cold_hands_and_feets", "lethargy"}, "Hypothyroidism"),
    ({"joint_pain", "neck_pain", "swelling_joints"}, "Arthritis"),
    ({"joint_pain", "knee_pain", "painful_walking"}, "Osteoarthristis"),

    # ==========================================
    # 8. UROLOGICAL
    # ==========================================
    ({"burning_micturition", "bladder_discomfort", "continuous_feel_of_urine"}, "Urinary tract infection"),
    ({"foul_smell_of urine", "bladder_discomfort", "burning_micturition"}, "Urinary tract infection"),

    # ==========================================
    # 9. CRITICAL / EMERGENCY (To trigger the safety interceptor)
    # ==========================================
    ({"chest_pain", "breathlessness", "sweating", "vomiting"}, "Heart attack"),
    ({"weakness_of_one_body_side", "vomiting", "headache", "altered_sensorium"}, "Paralysis (brain hemorrhage)")
]

def get_heuristic_diagnosis(extracted_symptoms):
    """
    Checks if the user's symptoms match our safe, hardcoded rules.
    Returns the disease name if found, otherwise returns None.
    """
    if not extracted_symptoms:
        return None
        
    user_syms = set(extracted_symptoms)
    
    for rule_syms, disease in COMMON_CASES:
        # EXACT MATCH: If the user types exactly these symptoms
        if rule_syms == user_syms:
            return disease
            
        # SUBSET MATCH: If the user has these core symptoms + maybe 1 extra minor thing
        if rule_syms.issubset(user_syms) and len(user_syms) <= len(rule_syms) + 1:
            return disease
            
    return None # If no rule matches, we let the ML model take over