import json
import os
import re
import time
import requests
import spacy
from spacy.matcher import PhraseMatcher
from bs4 import BeautifulSoup
import trafilatura

# Import your existing modules
from disease_list import DISEASES
from mappings import AYURVEDIC_MAPPING
from pdf_engine import extract_treatment_from_pdf

OUTPUT_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../data/ayurveda_kb_final.json")

# =====================================================================
# 1. NLP ONTOLOGY (GAZETTEER)
# =====================================================================
print("🧠 Loading spaCy NLP Model...")
nlp = spacy.load("en_core_web_sm")
matcher = PhraseMatcher(nlp.vocab, attr="LOWER")

# Expanded Dictionary (Teaches the AI what an Ayurvedic medicine is)
AYURVEDIC_HERBS = [
    "ashwagandha", "neem", "tulsi", "turmeric", "giloy", "amla", "triphala", 
    "guduchi", "shatavari", "brahmi", "arjuna", "guggulu", "shilajit", "licorice", 
    "yashtimadhu", "haridra", "ginger", "pippali", "cardamom", "clove", "sandalwood", 
    "aloe vera", "bhringraj", "manjistha", "kutki", "chirata", "kalmegh", "punarnava", 
    "gokshura", "vacha", "lodhra", "dhanyaka", "shallaki", "bhumyamalaki", "katuki", 
    "pushkarmool", "rasna", "dashamula", "bala", "vidari", "kapikacchu", "shankhapushpi", 
    "jatamansi", "musta", "sariva", "usheera", "chandana", "papaya leaf", "gandhak",
    "haritaki", "bibhitaki", "maricha", "shunti", "kumari", "bakuchi", "khadira",
    "kamadudha", "avipattikar", "sutashekhar", "haridra khanda", "mahasudarshan"
]

patterns = [nlp.make_doc(text) for text in AYURVEDIC_HERBS]
matcher.add("AYU_HERBS", patterns)

FORMULATION_SUFFIXES = [r"\b[A-Z][a-z]+ Vati\b", r"\b[A-Z][a-z]+ Churna\b", r"\b[A-Z][a-z]+ Taila\b", 
                        r"\b[A-Z][a-z]+ Ghrita\b", r"\b[A-Z][a-z]+ Bhasma\b", r"\b[A-Z][a-z]+ Asava\b", 
                        r"\b[A-Z][a-z]+ Arishta\b", r"\b[A-Z][a-z]+ Kashayam\b", r"\b[A-Z][a-z]+ Rasa\b",
                        r"\b[A-Z][a-z]+ Kwath\b", r"\b[A-Z][a-z]+ Guggulu\b", r"\b[A-Z][a-z]+ Lepa\b"]

# =====================================================================
# 2. MULTI-SOURCE SCRAPERS (WEB + BOOK)
# =====================================================================
HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/91.0'}

def scrape_easyayurveda(query):
    """Scrapes full article text from EasyAyurveda."""
    try:
        url = f"https://www.easyayurveda.com/?s={query.replace(' ', '+')}"
        res = requests.get(url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(res.text, 'html.parser')
        link = soup.select_one('article h2 a') or soup.select_one('.entry-title a')
        if link and 'href' in link.attrs:
            print(f"      🔗 Deep Crawling: {link['href']}")
            downloaded = trafilatura.fetch_url(link['href'])
            return trafilatura.extract(downloaded)
    except:
        pass
    return ""

def search_duckduckgo_snippets(query):
    """Bypasses blocks to scrape top 10 search result summaries from the web."""
    try:
        print(f"      🌐 Web Search Fallback for: {query}")
        url = f"https://html.duckduckgo.com/html/?q={query.replace(' ', '+')}"
        res = requests.get(url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(res.text, 'html.parser')
        snippets = [a.text for a in soup.find_all('a', class_='result__snippet')]
        return " ".join(snippets)
    except:
        return ""

# =====================================================================
# 3. NLP EXTRACTION LOGIC
# =====================================================================
def extract_knowledge(raw_text):
    if not raw_text: return [], [], []
    
    doc = nlp(raw_text)
    medicines = set()
    precautions = set()
    prep_tips = set()
    
    # Extract Herbs
    matches = matcher(doc)
    for match_id, start, end in matches:
        medicines.add(doc[start:end].text.title())
        
    # Extract Formulations (Regex)
    for suffix in FORMULATION_SUFFIXES:
        for match in re.findall(suffix, raw_text, re.IGNORECASE):
            medicines.add(match.title())
            
    # Contextual Extraction (Sentences)
    for sent in doc.sents:
        s_text = sent.text.strip().replace('\n', ' ')
        if len(s_text) < 20 or len(s_text) > 300: continue
        lower_sent = s_text.lower()
        
        # Precaution mapping
        if any(w in lower_sent for w in ["avoid", "restrict", "do not eat", "contraindicated", "diet"]):
            precautions.add(s_text)
            
        # Preparation mapping
        if any(w in lower_sent for w in ["mix", "boil", "decoction", "powder", "paste", "water", "milk"]):
            # Only keep tip if it mentions a medicine we found
            if any(med.lower() in lower_sent for med in medicines):
                prep_tips.add(s_text)

    return list(medicines), list(precautions), list(prep_tips)

# =====================================================================
# 4. MASTER BUILD PIPELINE
# =====================================================================
def build_kb():
    print(f"\n🚀 INITIATING MULTI-SOURCE EXTRACTION ({len(DISEASES)} Diseases)\n")
    kb = {}

    for i, disease in enumerate(DISEASES):
        sanskrit_name = AYURVEDIC_MAPPING.get(disease, disease)
        print(f"[{i+1}/{len(DISEASES)}] Mining: {disease} ({sanskrit_name})")
        
        raw_pool = ""
        sources = []

        # --- SOURCE 1: THE BOOK (Sushruta/Charaka Samhita) ---
        print("      📖 Scanning PDF Books...")
        pdf_text = extract_treatment_from_pdf(disease, sanskrit_name)
        if pdf_text:
            raw_pool += pdf_text + "\n"
            sources.append("Sushruta Samhita (Book)")

        # --- SOURCE 2: EASY AYURVEDA ---
        web_data = scrape_easyayurveda(f"{sanskrit_name} treatment")
        if web_data:
            raw_pool += web_data + "\n"
            sources.append("EasyAyurveda")

        # RUN NLP ROUND 1
        meds, precs, preps = extract_knowledge(raw_pool)

        # --- SOURCE 3: WEB SEARCH (If Book + EasyAyurveda failed) ---
        if len(meds) < 2:
            snippet_data = search_duckduckgo_snippets(f"{disease} {sanskrit_name} best ayurvedic medicine herbs")
            if snippet_data:
                raw_pool += snippet_data + "\n"
                sources.append("Web Search Aggregation")
                # Re-run NLP with new web data
                meds, precs, preps = extract_knowledge(raw_pool)

        # Generate Standard Buy Links
        med_list = meds[:6]
        buy_links = [f"https://www.1mg.com/search/all?name={m.replace(' ', '+')}" for m in med_list]

        # Failsafe formatting (Ensures UI never breaks)
        if not precs: precs = ["Maintain a light, easily digestible diet.", "Avoid cold, heavy, and oily foods."]
        if not preps: preps = ["Consume herbs with warm water unless directed otherwise."]
        if not med_list: med_list = ["Triphala", "Ashwagandha"] # Absolute worst case fallback

        kb[disease] = {
            "medicine_names": med_list,
            "precautions": precs[:3],
            "preparation_tips": preps[:3],
            "buy_links": buy_links[:6],
            "source": " + ".join(set(sources))
        }
        
        print(f"      ✅ Extracted {len(med_list)} medicines from {len(sources)} sources.")
        time.sleep(1) # Prevent blocking

    # Save final JSON
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(kb, f, indent=4)
        
    print(f"\n🏆 DATASET GENERATED: {OUTPUT_FILE}")

if __name__ == "__main__":
    build_kb()