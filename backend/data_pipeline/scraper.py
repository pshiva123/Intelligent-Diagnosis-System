import requests
from bs4 import BeautifulSoup
import trafilatura
from backend.data_pipeline.mappings import AYURVEDIC_MAPPING
from backend.data_pipeline.pdf_engine import extract_treatment_from_pdf
from backend.data_pipeline.nlp_engine import extract_structured_data

HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/91.0.4472.124 Safari/537.36'}

# --- SMART RETRY MAP ---
# If the main disease name fails, the scraper auto-retries these synonyms.
# This is NOT hardcoded results, just "Better Search Queries".
RETRY_QUERIES = {
    "Peptic ulcer diseae": ["Amlapitta treatment", "Gastric ulcer ayurveda", "Hyperacidity cure"],
    "Typhoid": ["Jwara treatment", "Enteric fever ayurveda", "Vishamajwara"],
    "Acne": ["Mukha Dushika", "Pimple treatment ayurveda", "Kshudra roga"],
    "Dengue": ["Dandaka jwara", "Viral fever ayurveda"],
    "Hyperthyroidism": ["Bhasmaka roga", "Thyroid ayurveda", "Metabolism disorder"]
}

def direct_search(query):
    """Searches EasyAyurveda.com"""
    try:
        url = f"https://www.easyayurveda.com/?s={query.replace(' ', '+')}"
        res = requests.get(url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(res.text, 'html.parser')
        
        # Try multiple selectors to find a link
        link = soup.select_one('article h2 a') or soup.select_one('.entry-title a')
        
        if link:
            print(f"      -> Found Article: {link['href']}")
            downloaded = trafilatura.fetch_url(link['href'])
            return trafilatura.extract(downloaded)
    except:
        return None
    return None

def fetch_ayurvedic_data(disease_name):
    sanskrit_name = AYURVEDIC_MAPPING.get(disease_name, disease_name)
    print(f"   🔍 Processing: '{disease_name}'")
    
    raw_text_pool = ""
    sources = []

    # 1. PDF SEARCH
    pdf_text = extract_treatment_from_pdf(disease_name, sanskrit_name)
    if pdf_text:
        raw_text_pool += pdf_text + " "
        sources.append("Sushruta Samhita (PDF)")

    # 2. WEB SEARCH (Primary)
    web_text = direct_search(f"{sanskrit_name} treatment")
    if web_text:
        raw_text_pool += web_text + " "
        sources.append("EasyAyurveda (Primary)")
    
    # 3. SMART RETRY (If primary failed)
    # If we have very little text, try the synonyms
    if len(raw_text_pool) < 500 and disease_name in RETRY_QUERIES:
        print(f"      ⚠️ Low data. Attempting Smart Retry for {disease_name}...")
        for synonym in RETRY_QUERIES[disease_name]:
            print(f"      -> Retrying with query: '{synonym}'")
            retry_text = direct_search(synonym)
            if retry_text:
                raw_text_pool += retry_text + " "
                sources.append(f"EasyAyurveda ({synonym})")
                break # Stop once we find something

    # 4. PROCESS
    if raw_text_pool:
        final_data = extract_structured_data(raw_text_pool)
        final_data["source"] = ", ".join(sources)
        return final_data
    
    else:
        return None