from dataclasses import dataclass


@dataclass(frozen=True)
class Source:
    label: str
    url: str
    category: str


CLASSICAL_SOURCES = [
    Source("Charaka - Jwara Chikitsa", "https://www.easyayurveda.com/2015/08/10/charaka-jwara-chikitsa/", "classical"),
    Source("Charaka - Prameha Chikitsa", "https://www.easyayurveda.com/2015/08/24/charaka-prameha-chikitsa/", "classical"),
    Source("Charaka - Kushtha Chikitsa", "https://www.easyayurveda.com/2015/09/02/charaka-kushta-chikitsa/", "classical"),
    Source("Charaka - Grahani Chikitsa", "https://www.easyayurveda.com/2015/10/15/charaka-grahani-chikitsa/", "classical"),
    Source("Sushruta Samhita (Index)", "https://www.wisdomlib.org/hinduism/book/sushruta-samhita-volume-1-sutra-sthana", "classical"),
    Source("Sushruta - Chikitsa Sthana", "https://www.wisdomlib.org/hinduism/book/sushruta-samhita-volume-4-chikitsasthana", "classical"),
]


GOVERNMENT_SOURCES = [
    Source("Ministry of AYUSH", "https://www.ayush.gov.in/", "government"),
    Source("CCRAS", "https://www.ccras.nic.in/", "government"),
    Source("NAMASTE Portal", "https://namstp.ayush.gov.in/", "government"),
    Source("e-Aushadhi", "https://e-aushadhi.gov.in/", "government"),
]


DISEASES = [
    "Diabetes",
    "Bronchial Asthma",
    "Arthritis",
    "Migraine",
    "GERD",
    "Jaundice",
    "Urinary tract infection",
    "Psoriasis",
    "Common Cold",
    "Typhoid",
    "Dengue",
    "Malaria",
]


HERB_HINTS = [
    "ashwagandha", "guduchi", "amalaki", "haritaki", "bibhitaki", "triphala",
    "trikatu", "pippali", "shunthi", "haridra", "neem", "tulsi", "brahmi",
    "manjishtha", "sariva", "kutki", "punarnava", "guggulu", "arjuna",
    "karela", "gokshura", "sarpagandha", "bilva", "vasa", "yashtimadhu",
    "musta", "khadira", "kutaja", "bhumyamalaki", "shilajit", "dashamula",
]


DOSHA_HINTS = {
    "vata": ["vata", "dry", "pain", "stiff", "constipation", "tremor"],
    "pitta": ["pitta", "heat", "burning", "inflammation", "acidity", "jaundice"],
    "kapha": ["kapha", "phlegm", "mucus", "congestion", "heavy", "lethargy"],
}

