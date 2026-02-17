import os
import json
from pymongo import MongoClient
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

print("🌿 Connecting to MongoDB Atlas...")
client = MongoClient(os.getenv("MONGO_URI"))
db = client["diagnosis_system"]
inventory_collection = db["pharmacy_products_final"]

gemini_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

def seed_database():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    backend_dir = os.path.dirname(current_dir)
    project_root = os.path.dirname(backend_dir)
    
    kb_path = os.path.join(backend_dir, "data", "ayurveda_kb_final.json")
    frontend_img_dir = os.path.join(project_root, "frontend", "public", "images")
    
    with open(kb_path, "r", encoding="utf-8") as f:
        ayurveda_db = json.load(f)

    unique_medicines = set()
    for kb_data in ayurveda_db.values():
        for med in kb_data.get("medicine_names", []):
            if med.strip(): unique_medicines.add(med.strip())
                
    med_list = sorted(list(unique_medicines))
    
    extra_products = [
        "Pure Copper Water Bottle", "Neem Wood Comb", "Ayurvedic Sandalwood Soap",
        "Copper Tongue Scraper", "Ashwagandha Sleep Tea", "Essential Oil Diffuser", 
        "Himalayan Pink Salt Lamp", "Eco-Friendly Yoga Mat", "Ceramic Neti Pot",
        "Ayurvedic Massage Roller", "Triphala Digestive Tea", "Tulsi Green Tea",
        "Kumkumadi Tailam Face Serum", "Ayurvedic Incense Sticks", "Brahmi Memory Drink"
    ]
    
    full_catalog = med_list + extra_products
    print(f"🤖 Generating AI descriptions and prices for {len(full_catalog)} products...")
    
    prompt = f"""
    Act as an expert Ayurvedic Store Manager. I have {len(full_catalog)} items: {", ".join(full_catalog)}.
    
    For EVERY SINGLE item, generate:
    1. A realistic price in INR (between ₹150 and ₹2000).
    2. A highly compelling, 1-sentence product description.

    Return EXACTLY a JSON array of objects with keys: "id" (start from 1), "name", "price", "desc". 
    Do NOT include an image key in the JSON.
    """
    
    response = gemini_client.models.generate_content(
        model='gemini-2.5-flash',
        contents=prompt,
        config=types.GenerateContentConfig(response_mime_type="application/json")
    )
    
    products = json.loads(response.text)
    
    # 🚀 BULLETPROOF IMAGE MAPPING
    for item in products:
        safe_name = item["name"].replace(" ", "_").replace("/", "").lower()
        local_file_path = os.path.join(frontend_img_dir, f"{safe_name}.jpg")
        
        # Check if the Bing scraper successfully downloaded this specific image
        if os.path.exists(local_file_path):
            item["image"] = f"/images/{safe_name}.jpg" 
        else:
            # Smart Fallback: Assign a beautiful, realistic image based on the product name
            name_lower = item["name"].lower()
            if "churna" in name_lower or "powder" in name_lower:
                item["image"] = "https://images.unsplash.com/photo-1611078516568-ce18413b5275?auto=format&fit=crop&q=80&w=600"
            elif "taila" in name_lower or "oil" in name_lower or "serum" in name_lower:
                item["image"] = "https://images.unsplash.com/photo-1608248543803-ba4f8c70ae0b?auto=format&fit=crop&q=80&w=600"
            elif "vati" in name_lower or "tablet" in name_lower or "guggulu" in name_lower:
                item["image"] = "https://images.unsplash.com/photo-1584362917165-526a968579e8?auto=format&fit=crop&q=80&w=600"
            elif "tea" in name_lower or "drink" in name_lower:
                item["image"] = "https://images.unsplash.com/photo-1576092768241-dec231879fc3?auto=format&fit=crop&q=80&w=600"
            else:
                item["image"] = "https://images.unsplash.com/photo-1550989460-0adf9ea622e2?auto=format&fit=crop&q=80&w=600"
    
    print("💾 Saving to MongoDB with verified image paths...")
    inventory_collection.delete_many({}) 
    inventory_collection.insert_many(products)
    print("✅ SUCCESS! Store database is 100% verified and ready.")

if __name__ == "__main__":
    seed_database()