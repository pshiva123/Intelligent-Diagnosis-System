import os
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier, VotingClassifier
import xgboost as xgb
import joblib
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score

if not os.path.exists('models'):
    os.makedirs('models')

print("[+] Downloading Pristine Dataset from GitHub...")
DATASET_URL = "https://raw.githubusercontent.com/ParthPathak27/Disease-prediction-using-Machine-Learning/master/Training.csv"
df = pd.read_csv(DATASET_URL)

if 'Unnamed: 133' in df.columns:
    df = df.drop('Unnamed: 133', axis=1)

# =====================================================================
# 🛡️ CLINICAL SAFETY MEASURES (NEW)
# =====================================================================

# 1. REMOVE AIDS ENTIRELY: 
# Ayurveda does not treat HIV/AIDS. Removing it prevents the model from 
# ever predicting it and giving false hope or dangerous herbal advice.

df = df[df['prognosis'] != 'AIDS']
df = df.reset_index(drop=True)

# 2. DEFINE CRITICAL MEDICAL EMERGENCIES:
# We KEEP these in the training data so the AI can correctly identify them.
# However, we save this list as an artifact. In `main.py`, if the AI predicts 
# one of these, it will trigger an EMERGENCY protocol (Go to hospital) 
# instead of trying to sell them Ayurvedic medicines.
CRITICAL_DISEASES = [
    'Heart attack',
    'Paralysis (brain hemorrhage)'
]

joblib.dump(CRITICAL_DISEASES, 'models/critical_diseases.pkl')


# =====================================================================

X = df.drop('prognosis', axis=1)
y = df['prognosis']

le = LabelEncoder()
y_encoded = le.fit_transform(y)

X_train, X_test, y_train, y_test = train_test_split(
    X, y_encoded, test_size=0.2, random_state=42, stratify=y_encoded
)

# --- USER'S BRILLIANT NOISE INJECTION ---
np.random.seed(42)
X_test_noisy = X_test.copy().values

for i in range(len(X_test_noisy)):
    symptom_indices = np.where(X_test_noisy[i] == 1)[0]
    if len(symptom_indices) > 2:
        # Drop 1 or 2 symptoms randomly to simulate forgetful patients
        drop_count = np.random.randint(1, 3) 
        drop_idx = np.random.choice(symptom_indices, drop_count, replace=False)
        X_test_noisy[i, drop_idx] = 0

X_test_noisy_df = pd.DataFrame(X_test_noisy, columns=X.columns)

#
# --- IMPROVED XGBOOST WITH REGULARIZATION ---
xgb_model = xgb.XGBClassifier(
    max_depth=5,           # Reduced to prevent overfitting single symptoms
    learning_rate=0.05,    # Slower learning for better generalization
    n_estimators=150,
    reg_lambda=10,         # L2 Regularization to penalize extreme weights
    gamma=2,               # Minimum loss reduction to make a split
    random_state=42
)

rf_model = RandomForestClassifier(
    n_estimators=150,
    max_depth=8,
    min_samples_leaf=5,    # Ensures a diagnosis isn't based on 1-2 weird samples
    class_weight='balanced', 
    random_state=42
)

print("[+] Training Calibrated Gradient Boosting Engine...")
gb_model = GradientBoostingClassifier(
    n_estimators=200,       # More trees but smaller steps
    learning_rate=0.05,     # Slow down learning to prevent "memorizing" symptoms
    max_depth=4,            # Prevent deep, over-specialized trees
    min_samples_leaf=10,    # Requires a group of 10 samples to define a rule
    subsample=0.8,          # Use only 80% of data per tree to reduce overfitting
    max_features='sqrt',    # Only look at a random subset of symptoms for each split
    random_state=42
)

print("🤝 Combining Models into Soft-Voting Ensemble...")
ensemble_model = VotingClassifier(
    estimators=[
        ('xgb', xgb_model), 
        ('rf', rf_model), 
        ('gb', gb_model)
    ],
    voting='soft' 
)

# Train the Ensemble
ensemble_model.fit(X_train, y_train)

# Fit the XGBoost base model separately purely for the SHAP Explainer later
xgb_model.fit(X_train, y_train)

print("[+] Evaluating ENSEMBLE Model on Noisy Patient Data...")
y_pred = ensemble_model.predict(X_test_noisy_df)

accuracy = accuracy_score(y_test, y_pred)
precision = precision_score(y_test, y_pred, average='weighted', zero_division=0)
recall = recall_score(y_test, y_pred, average='weighted', zero_division=0)
f1 = f1_score(y_test, y_pred, average='weighted', zero_division=0)

# --- SAVE ARTIFACTS ---
joblib.dump(ensemble_model, 'models/ensemble_model.pkl')
joblib.dump(xgb_model, 'models/xgboost_base_model.pkl') 
joblib.dump(le, 'models/label_encoder.pkl')
joblib.dump(list(X.columns), 'models/symptoms_list.pkl')

print("\n=== CLINICAL ENSEMBLE EVALUATION METRICS ===")
print(f"Accuracy:  {accuracy * 100:.2f}%")
print(f"Precision: {precision * 100:.2f}%")
print(f"Recall:    {recall * 100:.2f}%")
print(f"F1-Score:  {f1 * 100:.2f}%")
print("=========================================\n")
print("SUCCESS: Master Artifacts securely saved to the 'models/' folder.")