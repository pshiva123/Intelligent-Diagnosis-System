import fitz  # PyMuPDF
import os
import re

# You MUST place the real PDF here: backend/data/books/sushruta.pdf
PDF_PATH = os.path.join(os.path.dirname(__file__), '../../backend/data/books/sushruta.pdf')

def extract_treatment_from_pdf(disease_term, sanskrit_term):
    """
    Scans the PDF for English OR Sanskrit terms using Fuzzy Regex.
    Returns the surrounding paragraph (Treatment Context).
    """
    print(f"      📖 Scanning PDF for: '{disease_term}' or '{sanskrit_term}'...")
    
    if not os.path.exists(PDF_PATH):
        print("      ❌ PDF file not found. Please add 'sushruta.pdf'.")
        return None

    try:
        doc = fitz.open(PDF_PATH)
        
        # We construct a regex that ignores case and handles hyphens
        # e.g., "Dadru" matches "Dadru", "Dadru-Kushta", "Dadru Kushta"
        pattern = re.compile(fr"({re.escape(disease_term)}|{re.escape(sanskrit_term)})", re.IGNORECASE)
        
        best_match = ""
        
        for page_num, page in enumerate(doc):
            text = page.get_text()
            
            # Find all matches on the page
            if pattern.search(text):
                # Locate the match
                match = pattern.search(text)
                idx = match.start()
                
                # EXTRACT CONTEXT: Get 500 chars before and 1500 chars after
                # This ensures we capture the "Treatment" section usually following the disease name
                start = max(0, idx - 500)
                end = min(len(text), idx + 1500)
                
                context = text[start:end].replace("\n", " ")
                
                # INTELLIGENT FILTER: Only keep if it mentions medical keywords
                if any(w in context.lower() for w in ['treatment', 'cure', 'medicine', 'remedy', 'paste', 'oil', 'decoction']):
                    best_match = f"...{context}..."
                    print(f"      ✅ Found relevant text on Page {page_num + 1}")
                    break # Stop after finding the first good treatment section

        doc.close()
        return best_match if best_match else None

    except Exception as e:
        print(f"      ❌ PDF Read Error: {e}")
        return None