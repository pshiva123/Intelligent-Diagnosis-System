from backend.data_pipeline.validator import verify_medicine

def verify_dataset(kb_data):
    """
    Loops through the generated dataset and tags medicines as 'Verified'
    if they exist in our valid herb dictionary.
    """
    verified_count = 0
    total_meds = 0
    
    for disease, data in kb_data.items():
        clean_meds = []
        
        for med in data.get("medicine_names", []):
            total_meds += 1
            # 1. Clean String
            med = med.replace("Use ", "").replace("Apply ", "").strip()
            
            # 2. Verify
            if verify_medicine(med):
                clean_meds.append(med) # It's valid
                verified_count += 1
            else:
                # If it looks like a formulation (Capitalized), keep it but mark unverified
                if med[0].isupper():
                    clean_meds.append(med + " (Unverified)")
        
        # Update with cleaned list
        data["medicine_names"] = clean_meds
        
        # Ensure precautions exist
        if not data.get("precautions"):
            data["precautions"] = ["Consult a Vaidya for specific diet restrictions."]

    print(f"🧐 CROSS-VERIFICATION REPORT:")
    print(f"   Checked {total_meds} medicines.")
    print(f"   Verified {verified_count} as authentic Ayurvedic terms.")
    
    return kb_data