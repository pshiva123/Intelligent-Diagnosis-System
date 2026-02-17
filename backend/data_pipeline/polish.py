import json
import os
import re

# --- CONFIGURATION ---
base_dir = os.path.dirname(os.path.abspath(__file__))
path_goated = os.path.join(base_dir, "../data/ayurveda_kb_goated.json")
path_final = os.path.join(base_dir, "../data/ayurveda_kb_final.json")

# --- GARBAGE FILTERS ---
# If a medicine starts with these, it's definitely an NLP error.
BAD_PREFIXES = [
    "Of ", "And ", "The ", "In ", "This ", "That ", "Dicated ", "Especially ", 
    "Once ", "If ", "For ", "With ", "Or ", "To ", "Consult ", "Use ", "Here ",
    "When ", "While ", "After ", "Before "
]

def clean_text(text):
    """
    Removes Unicode (Sanskrit/Hindi chars), extra spaces, and messy punctuation.
    """
    if not text: return ""
    # Remove Devanagari/Unicode characters (e.g., \u0926...)
    text = re.sub(r'[^\x00-\x7F]+', '', text)
    # Remove "Page XX" artifacts
    text = re.sub(r'Page\s+\d+', '', text)
    # Remove odd punctuation clusters like " .,"
    text = re.sub(r'\s+([?.!,"])', r'\1', text)
    # Remove leading/trailing punctuation
    text = text.strip(" .,-")
    # Collapse multiple spaces
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def is_valid_medicine(name):
    """
    Returns False if the medicine name looks like junk.
    """
    name = clean_text(name)
    
    # Check 1: Too short? (e.g. "Oil")
    if len(name) < 4: return False
    
    # Check 2: Starts with bad word?
    for bad in BAD_PREFIXES:
        if name.startswith(bad): return False
        
    # Check 3: Is it just a placeholder?
    if "Consult" in name or "Vaidya" in name: return False
    
    return True

def polish_dataset():
    print("✨ STARTING PURE POLISH (No Hardcoding)...")

    if not os.path.exists(path_goated):
        print("❌ Error: GOATED file not found. Run build_goated.py first.")
        return

    with open(path_goated, "r", encoding="utf-8") as f:
        kb_main = json.load(f)
        
    final_kb = {}
    
    for disease, data in kb_main.items():
        print(f"   Processing: {disease}...")
        
        # 1. CLEAN MEDICINES
        # We only keep medicines that pass the 'is_valid_medicine' check
        raw_meds = data.get("medicine_names", [])
        clean_meds = set()
        
        for m in raw_meds:
            # Remove "(Unverified)" tag
            m_clean = m.replace("(Unverified)", "").strip()
            if is_valid_medicine(m_clean):
                clean_meds.add(m_clean)
        
        # 2. CLEAN TIPS & PRECAUTIONS
        # Remove unicode and junk text from sentences
        clean_prep = []
        for tip in data.get("preparation_tips", []):
            cleaned_tip = clean_text(tip)
            # Only keep tips that are actual sentences (longer than 15 chars)
            if len(cleaned_tip) > 15: 
                clean_prep.append(cleaned_tip)
                
        clean_precautions = []
        for p in data.get("precautions", []):
            cleaned_p = clean_text(p)
            if len(cleaned_p) > 15:
                clean_precautions.append(cleaned_p)

        # 3. REGENERATE LINKS (Only for the valid medicines)
        final_meds_list = list(clean_meds)
        new_links = []
        for m in final_meds_list:
            new_links.append(f"https://www.1mg.com/search/all?name={m.replace(' ', '+')}")

        # 4. CONSTRUCT FINAL OBJECT
        # We perform NO manual insertions. If it's empty, it stays empty.
        final_kb[disease] = {
            "medicine_names": final_meds_list,
            "precautions": clean_precautions[:3],
            "preparation_tips": clean_prep[:3],
            "buy_links": new_links[:5],
            "source": data.get("source", "Unknown")
        }

    # 5. SAVE FINAL
    with open(path_final, "w", encoding="utf-8") as f:
        json.dump(final_kb, f, indent=4)
        
    print(f"\n🏆 FINAL CLEAN DATASET SAVED: {path_final}")
    print("   (Unicode removed, Junk filtered, Purely Extracted Data)")

if __name__ == "__main__":
    polish_dataset()