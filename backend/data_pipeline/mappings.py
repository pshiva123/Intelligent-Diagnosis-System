# Maps Kaggle Disease Names -> Ayurvedic Terminology
# This allows us to search authentic texts effectively.

AYURVEDIC_MAPPING = {
    "Fungal infection": "Dadru kushta",
    "Allergy": "Udarda shitapitta",
    "GERD": "Amlapitta",
    "Chronic cholestasis": "Kamala",
    "Drug Reaction": "Dushi visha",
    "Peptic ulcer diseae": "Parinamasula",
    "AIDS": "Ojakshaya",
    "Diabetes": "Madhumeha",
    "Gastroenteritis": "Visuchika",
    "Bronchial Asthma": "Tamaka shwasa",
    "Hypertension": "Raktagata vata",
    "Migraine": "Ardhavabhedaka",
    "Cervical spondylosis": "Greeva stambha",
    "Paralysis (brain hemorrhage)": "Pakshaghata",
    "Jaundice": "Kamala",
    "Malaria": "Vishama jwara",
    "Chicken pox": "Laghu masurika",
    "Dengue": "Dandaka jwara",
    "Typhoid": "Manthara jwara",
    "hepatitis A": "Kamala",
    "Hepatitis B": "Kamala",
    "Hepatitis C": "Kamala",
    "Hepatitis D": "Kamala",
    "Hepatitis E": "Kamala",
    "Alcoholic hepatitis": "Madatyaya",
    "Tuberculosis": "Rajayakshma",
    "Common Cold": "Pratishyaya",
    "Pneumonia": "Shwasa roga",
    "Dimorphic hemmorhoids(piles)": "Arsha",
    "Heart attack": "Hridroga",
    "Varicose veins": "Siragranthi",
    "Hypothyroidism": "Galaganda",
    "Hyperthyroidism": "Bhasmaka roga",
    "Hypoglycemia": "Madhumeha janya",
    "Osteoarthristis": "Sandhivata",
    "Arthritis": "Amavata",
    "(vertigo) Paroymsal  Positional Vertigo": "Bhrama",
    "Acne": "Yauvana pidaka",
    "Urinary tract infection": "Mutrakrichra",
    "Psoriasis": "Kitibha kushta",
    "Impetigo": "Visphota",
    # ... keep others same ...
    "Peptic ulcer diseae": "Parinamasula Amlapitta", # Broader search term
    "Typhoid": "Jwara", # 'Manthara Jwara' is rare, 'Jwara' (Fever) will find remedies
    "Acne": "Mukha Dushika", # 'Yauvana Pidaka' failed, this is the common synonym
    # ... keep others same ...
}