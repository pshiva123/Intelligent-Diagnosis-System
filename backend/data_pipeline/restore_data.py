import urllib.request
import os

# --- PATHS ---
current_dir = os.path.dirname(os.path.abspath(__file__))
data_path = os.path.join(current_dir, "../data/Training.csv")

# The raw URL of the original, untouched Kaggle dataset hosted on GitHub
url = "https://raw.githubusercontent.com/itachi9604/healthcare-chatbot/master/Data/Training.csv"

def restore_original_data():
    print("🌐 Connecting to GitHub to fetch the original Kaggle dataset...")
    try:
        urllib.request.urlretrieve(url, data_path)
        print(f"✅ SUCCESS! Pristine dataset restored at: {data_path}")
        print("   You can now train the GOATED Naive Bayes model.")
    except Exception as e:
        print(f"❌ Network Error: {e}")

if __name__ == "__main__":
    restore_original_data()