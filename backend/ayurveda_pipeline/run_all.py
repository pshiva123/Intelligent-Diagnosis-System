import json
import sys
from pathlib import Path

G="\033[92m"; Y="\033[93m"; C="\033[96m"; R="\033[91m"; B="\033[1m"; X="\033[0m"

def banner(t): print(f"\n{B}{C}{'='*55}\n  {t}\n{'='*55}{X}\n")

def demo():
    banner("LIVE DEMO - Patient-Specific Medicine Routing")
    kb_path = Path("output/ayurveda_kb_final.json")
    if not kb_path.exists():
        print(f"{R}  Run full pipeline first{X}"); return
    records = json.load(open(kb_path, encoding="utf-8"))

    def age_group(age):
        return "young" if age < 25 else ("elder" if age >= 60 else "middle")

    def get_meds(disease, age, gender, severity):
        ag = age_group(age)
        candidates = [
            r for r in records
            if r["disease"] == disease
            and r["severity"] == severity
            and r["gender"] in (gender, "all")
            and r["age_group"] in (ag, "all")
        ]
        if not candidates:
            candidates = [r for r in records if r["disease"] == disease and r["severity"] == severity]
        return candidates[:3]

    TESTS = [
        ("Diabetes",         45, "female", "medium"),
        ("Diabetes",         10, "male",   "low"),
        ("Diabetes",         68, "female", "high"),
        ("Bronchial Asthma", 14, "male",   "medium"),
        ("Bronchial Asthma", 52, "female", "high"),
        ("Arthritis",        65, "male",   "medium"),
        ("Acne",             19, "female", "medium"),
        ("Malaria",          28, "female", "medium"),
        ("Fungal infection", 35, "male",   "high"),
        ("Urinary tract infection", 30, "female", "medium"),
    ]

    print(f"  {'Patient':<40}  Medicines\n  {'-'*75}")
    for disease, age, gender, severity in TESTS:
        ag   = age_group(age)
        meds = get_meds(disease, age, gender, severity)
        info = f"{ag} ({age}y) {gender} | {disease} | {severity}"
        print(f"\n  {B}{info}{X}")
        if meds:
            for i, m in enumerate(meds, 1):
                print(f"    [{i}] {G}{m['medicine_name']}{X} ({m['formulation_type']}) - {m['dosage'][:55]}")
                print(f"        herbs: {', '.join(m['herb_sanskrit'][:3])}")
        else:
            print(f"    {Y}No matching medicine for this profile{X}")
    print()

def main():
    args = sys.argv[1:]
    banner("AYURVEDIC DATASET PIPELINE")
    print("  Source priority: Classical texts -> Govt portals -> Google fallback")
    print("  Then: NLP extraction -> Structured KB dataset\n")

    if "--demo" in args:
        demo(); return

    print(f"{B}{Y}[STEP 0] Environment{X}")
    import platform; print(f"  Python {platform.python_version()}")
    try:
        import torch; print(f"  PyTorch {torch.__version__} | {'GPU OK' if torch.cuda.is_available() else 'CPU'}")
        import transformers; print(f"  {G}OK Transformers {transformers.__version__}{X}")
    except ImportError as e:
        print(f"{R}  Missing: {e}\n  pip install torch transformers requests beautifulsoup4{X}"); sys.exit(1)

    print(f"\n{B}{Y}[STEP 1] Data Collection{X}")
    import step1_scrapper
    scraped = step1_scrapper.run()
    if not scraped:
        print(f"{R}  No chapters scraped. Check internet.{X}"); sys.exit(1)

    print(f"\n{B}{Y}[STEP 2] NLP Extraction{X}")
    import step2_biobert_extractor
    step2_biobert_extractor.run()

    print(f"\n{B}{Y}[STEP 3] Build Dataset{X}")
    import step3_build_kb
    step3_build_kb.run()

    demo()
    banner("PIPELINE COMPLETE")
    print(f"  {G}scraped_texts/raw_corpus.json{X}")
    print(f"  {G}extracted_data/biobert_extractions.json{X}")
    print(f"  {G}output/ayurveda_kb_structured.json{X}")
    print(f"  {G}output/ayurveda_kb_final.json{X}")
    print(f"  {G}output/kb_quality_report.json{X}")
    print(f"  {G}medicine_master.json{X}\n")

if __name__ == "__main__":
    main()