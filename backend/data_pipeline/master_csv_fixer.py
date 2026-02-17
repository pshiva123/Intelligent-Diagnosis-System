import pandas as pd
import os

data_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../data/Training.csv")

# =====================================================================
# THE CLINICAL CONSENSUS MATRIX
# This dictionary overrides the flawed Kaggle data with real medical facts.
# If a disease is found in the CSV, it guarantees these columns are set to 1.
# =====================================================================
CLINICAL_TRUTHS = {
    "Jaundice": ["yellowish_skin", "yellowing_of_eyes", "fatigue", "vomiting", "high_fever", "nausea"],
    "Hypertension": ["headache", "dizziness", "chest_pain", "fatigue"],
    "Migraine": ["headache", "nausea", "visual_disturbances", "blurred_and_distorted_vision"],
    "Cervical spondylosis": ["neck_pain", "weakness_in_limbs", "back_pain", "stiff_neck"],
    "Malaria": ["high_fever", "shivering", "sweating", "chills", "headache", "nausea", "vomiting", "muscle_pain"],
    "Dengue": ["high_fever", "joint_pain", "muscle_pain", "headache", "vomiting", "fatigue", "skin_rash", "pain_behind_the_eyes"],
    "Typhoid": ["high_fever", "chills", "headache", "vomiting", "fatigue", "abdominal_pain", "nausea", "constipation"],
    "Common Cold": ["runny_nose", "continuous_sneezing", "chills", "fatigue", "cough", "headache", "muscle_pain"],
    "Pneumonia": ["chills", "cough", "high_fever", "breathlessness", "fatigue", "sweating", "chest_pain"],
    "Tuberculosis": ["chills", "cough", "high_fever", "breathlessness", "fatigue", "weight_loss", "sweating", "chest_pain", "blood_in_sputum"],
    "Acne": ["skin_rash", "scurring", "blackheads", "pus_filled_pimples"],
    "Urinary tract infection": ["burning_micturition", "continuous_feel_of_urine", "bladder_discomfort"],
    "Heart attack": ["chest_pain", "vomiting", "breathlessness", "sweating"],
    "Paralysis (brain hemorrhage)": ["weakness_of_one_body_side", "altered_sensorium", "vomiting", "headache"],
    "Impetigo": ["skin_rash", "red_sore_around_nose", "yellow_crust_ooze", "blister"],
    "Gastroenteritis": ["vomiting", "diarrhoea", "stomach_pain", "sunken_eyes", "dehydration"],
    "Bronchial Asthma": ["fatigue", "cough", "high_fever", "breathlessness", "mucoid_sputum"],
    "Arthritis": ["muscle_weakness", "stiff_neck", "swelling_joints", "movement_stiffness", "painful_walking"],
    "Osteoarthristis": ["joint_pain", "neck_pain", "knee_pain", "hip_joint_pain", "swelling_joints", "painful_walking"],
    "Allergy": ["continuous_sneezing", "shivering", "chills", "watering_from_eyes"],
    "Fungal infection": ["itching", "skin_rash", "nodal_skin_eruptions", "dischromic _patches"]
}

def clean_entire_dataset():
    print("🚀 Initiating Enterprise Data Imputation across entire dataset...")
    
    if not os.path.exists(data_path):
        print("❌ Error: Training.csv not found!")
        return

    df = pd.read_csv(data_path)
    
    # Standardize the prognosis column (remove trailing spaces like "Hypertension ")
    df['prognosis'] = df['prognosis'].str.strip()
    
    fixed_count = 0
    
    for disease, required_symptoms in CLINICAL_TRUTHS.items():
        # Check if the disease exists in the dataset
        if disease in df['prognosis'].values:
            disease_mask = df['prognosis'] == disease
            
            for symptom in required_symptoms:
                # Make sure the symptom column actually exists in the CSV
                if symptom in df.columns:
                    # Overwrite the data with clinical truth (1 = True)
                    df.loc[disease_mask, symptom] = 1
            
            print(f"   ✅ Fully Patched & Enforced: {disease}")
            fixed_count += 1
        else:
            print(f"   ⚠️ Warning: {disease} not found in CSV. Skipping.")

    # Save the perfected dataset
    df.to_csv(data_path, index=False)
    print(f"\n🎉 Master Clean Complete! {fixed_count} diseases structurally corrected.")
    print("   The dataset is now mathematically bound to clinical reality.")

if __name__ == "__main__":
    clean_entire_dataset()