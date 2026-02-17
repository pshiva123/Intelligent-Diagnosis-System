import re

# --- 1. ROBUST PATTERNS (Regex) ---
# We use regex to catch any medicine ending in these standard Ayurvedic suffixes.
FORMULATION_SUFFIXES = [
    r"\b[A-Z][a-z]+ Vati\b",
    r"\b[A-Z][a-z]+ Churna\b",
    r"\b[A-Z][a-z]+ Bhasma\b",
    r"\b[A-Z][a-z]+ Taila\b",
    r"\b[A-Z][a-z]+ Tailam\b",
    r"\b[A-Z][a-z]+ Ghrita\b",
    r"\b[A-Z][a-z]+ Ghritam\b",
    r"\b[A-Z][a-z]+ Ras\b",
    r"\b[A-Z][a-z]+ Rasa\b",
    r"\b[A-Z][a-z]+ Arishta\b",
    r"\b[A-Z][a-z]+ Asava\b",
    r"\b[A-Z][a-z]+ Kwath\b",
    r"\b[A-Z][a-z]+ Kashayam\b",
    r"\b[A-Z][a-z]+ Guggulu\b",
    r"\b[A-Z][a-z]+ Lehya\b"
]

# Common single herbs to scan for (Case Insensitive)
COMMON_HERBS = [
    "Ashwagandha", "Neem", "Tulsi", "Turmeric", "Giloy", "Amla", "Ginger", 
    "Garlic", "Aloe Vera", "Sandalwood", "Licorice", "Brahmi", "Arjuna", 
    "Shilajit", "Guduchi", "Manjistha", "Kutki", "Punarnava", "Haridra", 
    "Triphala", "Trikatu", "Shatavari", "Bhringraj", "Kalmegh"
]

PRECAUTION_KEYWORDS = ["avoid", "do not", "restrict", "contraindicated", "abstain", "harmful", "reduce"]
PREP_KEYWORDS = ["mix", "boil", "paste", "decoction", "powder", "warm water", "milk", "honey", "drink", "apply", "grind"]

def clean_text(text):
    text = re.sub(r'Page\s+\d+', '', text) # Remove Page numbers
    text = text.replace('-\n', '').replace('\n', ' ') # Fix broken lines
    text = re.sub(r'\s+', ' ', text) # Remove double spaces
    return text.strip()

def extract_structured_data(raw_text):
    text = clean_text(raw_text)
    
    medicines = set()
    precautions = []
    prep_tips = []
    
    # --- 1. EXTRACT FORMULATIONS (Regex) ---
    for pattern in FORMULATION_SUFFIXES:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for match in matches:
            medicines.add(match.title()) # Capitalize nicely

    # --- 2. EXTRACT HERBS (Keywords) ---
    for herb in COMMON_HERBS:
        if re.search(fr"\b{herb}\b", text, re.IGNORECASE):
            medicines.add(herb)

    # --- 3. EXTRACT CONTEXT (Precautions & Prep) ---
    # Split by periods to get sentences
    sentences = re.split(r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?)\s', text)
    
    for sent in sentences:
        lower_sent = sent.lower()
        if len(sent) < 15 or len(sent) > 300: continue 

        # Precautions
        if any(k in lower_sent for k in PRECAUTION_KEYWORDS):
            precautions.append(sent.strip())

        # Preparation Tips
        if any(k in lower_sent for k in PREP_KEYWORDS):
            prep_tips.append(sent.strip())

    # --- 4. GENERATE LINKS ---
    buy_links = []
    for med in list(medicines)[:5]: 
        link = f"https://www.1mg.com/search/all?name={med.replace(' ', '+')}"
        buy_links.append(link)

    # Convert set to list for JSON serialization
    medicine_list = list(medicines)

    # Fallback if nothing found
    if not medicine_list:
        medicine_list.append("Consult a certified Ayurvedic Vaidya")

    return {
        "medicine_names": medicine_list[:6],      # KEY NAME: medicine_names
        "precautions": precautions[:3],           # KEY NAME: precautions
        "preparation_tips": prep_tips[:3],        # KEY NAME: preparation_tips
        "buy_links": buy_links                    # KEY NAME: buy_links
    }