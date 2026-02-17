import pandas as pd
import pickle
import os
from sklearn.naive_bayes import MultinomialNB
from sklearn.preprocessing import LabelEncoder

# --- PATHS ---
current_dir = os.path.dirname(os.path.abspath(__file__))
data_path = os.path.join(current_dir, "../data/Training.csv") # Make sure this is your ORIGINAL Kaggle CSV!
model_path = os.path.join(current_dir, "../models/disease_model.pkl")
encoder_path = os.path.join(current_dir, "../models/label_encoder.pkl")
features_path = os.path.join(current_dir, "../models/symptom_features.pkl")

print("🚀 Initializing Training Pipeline...")

# 1. Load the ORIGINAL Kaggle Dataset
df = pd.read_csv(data_path)
df['prognosis'] = df['prognosis'].str.strip() # Clean trailing spaces

# 2. Separate Features (X) and Target (y)
X = df.drop(columns=['prognosis'])
y = df['prognosis']

# 3. Encode the Target Labels
le = LabelEncoder()
y_encoded = le.fit_transform(y)

# 4. Train the GOATED Model: Multinomial Naive Bayes
print("🧠 Training Multinomial Naive Bayes Model...")
model = MultinomialNB()
model.fit(X, y_encoded)

# 5. Save the Model, Encoder, and Feature Names
os.makedirs(os.path.dirname(model_path), exist_ok=True)

with open(model_path, "wb") as f:
    pickle.dump(model, f)

with open(encoder_path, "wb") as f:
    pickle.dump(le, f)

with open(features_path, "wb") as f:
    pickle.dump(list(X.columns), f)

print("🎉 Naive Bayes Model Trained Successfully!")