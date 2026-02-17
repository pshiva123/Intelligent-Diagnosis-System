import json
import os
import re

# --- PATHS ---
current_dir = os.path.dirname(os.path.abspath(__file__))
data_path = os.path.join(current_dir, "../data/ayurveda_kb_final.json")

# Words that trick the Regex into thinking they are medicines
BAD_PREFIXES = r"^(The|Of|In|And|Like|If|This|A|An|Consult|Old|Specific|Also)\b\s*"

def clean_medicine_name(med):
    """Removes junk prefixes and ensures the medicine name is valid."""
    # Remove bad prefixes (case-insensitive)
    clean_med = re.sub(BAD_PREFIXES, "", med, flags=re.IGNORECASE).strip()
    
    # If the remaining word is too short or is JUST a suffix (e.g., "Lepa" or "Ghrita" by itself)
    if len(clean_med) < 4 or clean_med.lower() in ['lepa', 'ghrita', 'taila', 'churna', 'rasa', 'vati', 'kashayam', 'kwath']:
        return None
        
    return clean_med

def clean_sentence(text):
    """Scrubs Unicode, website artifacts, and formatting junk from sentences."""
    if not text:
        return None
        
    # 1. Remove all Devanagari/Sanskrit Unicode characters (\u0900 to \u097F)
    text = re.sub(r'[\u0900-\u097F]+', '', text)
    
    # 2. Remove table artifacts (|, ||) and email protection scripts
    text = re.sub(r'\|+', '', text)
    text = re.sub(r'\[email\s*protected\]', '', text, flags=re.IGNORECASE)
    
    # 3. Remove website navigation links (e.g., "Read - Ayurveda Lifestyle...")
    text = re.sub(r'Read\s*[\u2013\-]?\s*.*', '', text, flags=re.IGNORECASE)
    
    # 4. Remove floating numbers from lists (e.g., "1. ", "- ")
    text = re.sub(r'^[\d\.\-\*]+\s*', '', text)
    
    # 5. Clean up multiple spaces and hanging punctuation
    text = re.sub(r'\s+', ' ', text)
    text = text.strip(" -–,;")
    
    # 6. Quality Check: Is it a real sentence?
    # If it's too short (under 20 chars) or has no letters, drop it.
    if len(text) < 20 or not re.search('[a-zA-Z]', text):
        return None
        
    # Capitalize first letter and ensure it ends with a period
    text = text[0].upper() + text[1:]
    if not text.endswith('.') and not text.endswith('?'):
        text += '.'
        
    return text

def sanitize_dataset():
    print("🧼 STARTING DATA SANITIZATION...")
    
    if not os.path.exists(data_path):
        print(f"❌ Error: {data_path} not found.")
        return

    with open(data_path, "r", encoding="utf-8") as f:
        kb = json.load(f)
        
    total_meds_removed = 0
    total_sentences_fixed = 0

    for disease, data in kb.items():
        # --- 1. CLEAN MEDICINES ---
        raw_meds = data.get("medicine_names", [])
        clean_meds = []
        for med in raw_meds:
            cleaned = clean_medicine_name(med)
            if cleaned:
                clean_meds.append(cleaned)
            else:
                total_meds_removed += 1
                
        # --- 2. CLEAN PRECAUTIONS ---
        raw_precs = data.get("precautions", [])
        clean_precs = []
        for prec in raw_precs:
            cleaned = clean_sentence(prec)
            if cleaned:
                clean_precs.append(cleaned)
                total_sentences_fixed += 1
                
        # --- 3. CLEAN PREPARATION TIPS ---
        raw_tips = data.get("preparation_tips", [])
        clean_tips = []
        for tip in raw_tips:
            cleaned = clean_sentence(tip)
            if cleaned:
                clean_tips.append(cleaned)
                total_sentences_fixed += 1

        # --- 4. REGENERATE CLEAN BUY LINKS ---
        buy_links = [f"https://www.1mg.com/search/all?name={m.replace(' ', '+')}" for m in clean_meds[:6]]

        # Update the dictionary
        kb[disease]["medicine_names"] = clean_meds[:6]
        kb[disease]["precautions"] = list(set(clean_precs))[:3] # Set removes duplicates
        kb[disease]["preparation_tips"] = list(set(clean_tips))[:3]
        kb[disease]["buy_links"] = buy_links

    # Save the sanitized data back to the same file
    with open(data_path, "w", encoding="utf-8") as f:
        json.dump(kb, f, indent=4)

    print(f"✅ SANITIZATION COMPLETE.")
    print(f"   - Removed {total_meds_removed} junk medicine names (e.g. 'In Lepa').")
    print(f"   - Scrubbed and formatted {total_sentences_fixed} sentences (Removed Unicode & Artifacts).")
    print(f"   - Pristine data saved to {data_path}.")

if __name__ == "__main__":
    sanitize_dataset()