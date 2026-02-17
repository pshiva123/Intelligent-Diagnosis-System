# A list of valid Ayurvedic terms used ONLY for verifying extracted text.
# We do not pull data from here; we only check against it.

VALID_HERBS = {
    "ashwagandha", "neem", "tulsi", "turmeric", "giloy", "amla", "triphala", 
    "guduchi", "shatavari", "brahmi", "arjuna", "guggulu", "shilajit", "licorice", 
    "yashtimadhu", "haridra", "ginger", "pippali", "cardamom", "clove", "sandalwood", 
    "aloe vera", "bhringraj", "manjistha", "kutki", "chirata", "kalmegh", "punarnava", 
    "gokshura", "kaishore", "chandraprabha", "arogyavardhini", "sanjivani", 
    "tribhuvana", "sitopaladi", "avipattikar", "mahanarayan", "khadirarishta", 
    "dashamularishta", "ashokarishta", "kumaryasava", "chyawanprash", "vacha", 
    "lodhra", "dhanyaka", "gandhak", "rasayan", "bhasma", "pishti", "lauha", 
    "mandur", "parpati", "prakara", "taila", "ghrita", "churna", "kashayam", 
    "arishta", "asava", "vati", "gutika", "rasa", "lepa", "anjana", "nasyam",
    "mahasudarshan", "kanchanara", "sahachara", "balashwagandha", "dhanwantharam",
    "kottamchukkadi", "murivenna", "anu taila", "shadbindu", "kunkumadi"
}

def verify_medicine(med_name):
    """
    Returns True only if the medicine contains a valid Ayurvedic term.
    This filters out junk NLP results like 'Page 10' or 'The Doctor'.
    """
    parts = med_name.lower().replace('-', ' ').split()
    for part in parts:
        if part in VALID_HERBS:
            return True
    return False