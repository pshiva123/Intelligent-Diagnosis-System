import sys
import types

# 🚀 PYTHON 3.13 HACK: Create a fake 'imghdr' module so bing_image_downloader doesn't crash!
fake_imghdr = types.ModuleType('imghdr')
fake_imghdr.what = lambda file, h=None: "jpeg" # Tell the library every downloaded file is a valid image
sys.modules['imghdr'] = fake_imghdr
# ---------------------------------------------------------

import os
import json
import shutil
from bing_image_downloader import downloader

def download_medicine_images():
    # 1. Setup paths
    current_dir = os.path.dirname(os.path.abspath(__file__))
    backend_dir = os.path.dirname(current_dir)
    project_root = os.path.dirname(backend_dir)
    
    frontend_img_dir = os.path.join(project_root, "frontend", "public", "images")
    kb_path = os.path.join(backend_dir, "data", "ayurveda_kb_final.json")
    
    os.makedirs(frontend_img_dir, exist_ok=True)
    print(f"📁 Saving real images to: {frontend_img_dir}")
    
    try:
        with open(kb_path, "r", encoding="utf-8") as f:
            ayurveda_db = json.load(f)
    except Exception as e:
        print(f"❌ Could not find JSON database at {kb_path}\nError: {e}")
        return
        
    unique_medicines = set()
    for kb_data in ayurveda_db.values():
        for med in kb_data.get("medicine_names", []):
            if med.strip(): unique_medicines.add(med.strip())
            
    medicines = sorted(list(unique_medicines))
    
    extra_products = [
        "Pure Copper Water Bottle", "Neem Wood Comb", "Ayurvedic Sandalwood Soap",
        "Copper Tongue Scraper", "Ashwagandha Sleep Tea", "Essential Oil Diffuser", 
        "Himalayan Pink Salt Lamp", "Eco-Friendly Yoga Mat", "Ceramic Neti Pot",
        "Ayurvedic Massage Roller", "Triphala Digestive Tea", "Tulsi Green Tea",
        "Kumkumadi Tailam Face Serum", "Ayurvedic Incense Sticks", "Brahmi Memory Drink"
    ]
    
    full_catalog = medicines + extra_products
    print(f"🤖 Searching BING for {len(full_catalog)} products...\n")
    
    for item in full_catalog:
        safe_name = item.replace(" ", "_").replace("/", "").lower()
        final_file_path = os.path.join(frontend_img_dir, f"{safe_name}.jpg")
        
        # Skip if we already successfully downloaded it from the previous DuckDuckGo attempt!
        if os.path.exists(final_file_path):
            print(f"✅ Already exists: {item}")
            continue
            
        search_query = f"{item} ayurvedic product"
        print(f"⬇️ Downloading: {item}...")
        
        try:
            # Bing downloader creates a folder named after the query
            downloader.download(search_query, limit=1, output_dir=frontend_img_dir, adult_filter_off=False, force_replace=False, timeout=15, verbose=False)
            
            downloaded_folder = os.path.join(frontend_img_dir, search_query)
            
            # Move the downloaded image out of the folder and rename it properly
            if os.path.exists(downloaded_folder):
                downloaded_files = os.listdir(downloaded_folder)
                if downloaded_files:
                    src_file = os.path.join(downloaded_folder, downloaded_files[0])
                    shutil.move(src_file, final_file_path)
                
                # Cleanup the empty folder Bing created
                os.rmdir(downloaded_folder)
                print(f"✅ Success: {item}")
        except Exception as e:
            print(f"❌ Failed to download {item}: {e}")
            
    print("\n🎉 BING DOWNLOAD PROCESS COMPLETE!")

if __name__ == "__main__":
    download_medicine_images()