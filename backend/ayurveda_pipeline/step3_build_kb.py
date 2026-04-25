import json
from collections import defaultdict
from pathlib import Path

from pipeline_config import DISEASES

AGES = ["young", "middle", "elder"]
GENDERS = ["male", "female"]
SEVERITIES = ["low", "medium", "high"]


def build_contraindications(constraints: dict) -> list[str]:
    out = []
    if not constraints.get("child_safe", True):
        out.append("Not recommended for children under 12")
    if not constraints.get("elderly_safe", True):
        out.append("Use with caution in elderly")
    if not constraints.get("pregnant_safe", True):
        out.append("Avoid in pregnancy")
    return out


def dosage_from_severity(severity: str) -> str:
    if severity == "high":
        return "Intensive protocol - physician supervision required"
    if severity == "low":
        return "Low intensity protocol - once or twice daily"
    return "Standard protocol - twice daily after meals"


def infer_formulation(herbs: list[str]) -> str:
    if len(herbs) >= 5:
        return "kwatha"
    if len(herbs) >= 3:
        return "churna"
    return "vati"


def build_master_from_extractions(extractions: list[dict]) -> dict:
    grouped = defaultdict(list)
    for item in extractions:
        herbs = item.get("herbs_found", [])
        diseases = item.get("diseases", [])
        if not herbs or not diseases:
            continue
        for disease in diseases:
            grouped[disease].append(item)

    master = {}
    for disease in DISEASES:
        disease_items = grouped.get(disease, [])
        herb_counter = defaultdict(int)
        source_counter = defaultdict(int)
        dosha_counter = defaultdict(int)
        constraints = {"child_safe": True, "elderly_safe": True, "pregnant_safe": True}
        confidence_total = 0.0

        for row in disease_items:
            for herb in row.get("herbs_found", []):
                herb_counter[herb] += 1
            source_counter[row.get("source_url", "")] += 1
            dosha_counter[row.get("dosha_type", "tridosha")] += 1
            c = row.get("constraints", {})
            constraints["child_safe"] = constraints["child_safe"] and c.get("child_safe", True)
            constraints["elderly_safe"] = constraints["elderly_safe"] and c.get("elderly_safe", True)
            constraints["pregnant_safe"] = constraints["pregnant_safe"] and c.get("pregnant_safe", True)
            confidence_total += float(row.get("confidence_score", 0.6))

        top_herbs = [h for h, _ in sorted(herb_counter.items(), key=lambda x: x[1], reverse=True)[:6]]
        if not top_herbs:
            top_herbs = ["guduchi", "triphala"]
        best_source = max(source_counter, key=source_counter.get) if source_counter else "N/A"
        best_dosha = max(dosha_counter, key=dosha_counter.get) if dosha_counter else "tridosha"
        avg_conf = round(confidence_total / max(len(disease_items), 1), 3)

        master[disease] = {
            "medicine_name": f"{disease} Ayurvedic Protocol",
            "formulation_type": infer_formulation(top_herbs),
            "herb_sanskrit": top_herbs,
            "dosha_type": best_dosha,
            "source": best_source,
            "confidence_score": avg_conf,
            "constraints": constraints,
            "evidence_count": len(disease_items),
        }
    return master


def run():
    print("=" * 65)
    print("STEP 3 - Build Final Ayurvedic KB Dataset")
    print("=" * 65)

    extraction_path = Path("extracted_data/biobert_extractions.json")
    if not extraction_path.exists():
        print("  ERROR: Run step2_biobert_extractor.py first.")
        return {}
    extractions = json.load(open(extraction_path, encoding="utf-8"))
    master = build_master_from_extractions(extractions)

    Path("output").mkdir(exist_ok=True)
    structured = {}
    flat = []
    missing_combos = []

    for disease, base in master.items():
        structured[disease] = {}
        for age in AGES:
            for gender in GENDERS:
                for severity in SEVERITIES:
                    combo = f"{age}_{gender}_{severity}"
                    contraindications = build_contraindications(base["constraints"])
                    dosage = dosage_from_severity(severity)
                    if age == "young" and not base["constraints"]["child_safe"]:
                        dosage = f"Half adult dose. {dosage}"
                    elif age == "elder":
                        dosage = f"Start with reduced dose. {dosage}"

                    record = {
                        "medicine_name": base["medicine_name"],
                        "herb_sanskrit": base["herb_sanskrit"],
                        "formulation_type": base["formulation_type"],
                        "dosha_type": base["dosha_type"],
                        "dosage": dosage,
                        "contraindications": contraindications,
                        "source": base["source"],
                        "confidence_score": base["confidence_score"],
                        "evidence_count": base["evidence_count"],
                    }
                    structured[disease][combo] = [record]
                    flat.append(
                        {
                            "disease": disease,
                            "age_group": age,
                            "gender": gender,
                            "severity": severity,
                            **record,
                        }
                    )
                    if base["evidence_count"] == 0:
                        missing_combos.append(f"{disease}:{combo}")

    quality = {
        "disease_count": len(structured),
        "total_combos_expected": len(structured) * len(AGES) * len(GENDERS) * len(SEVERITIES),
        "total_records": len(flat),
        "zero_evidence_combos": len(missing_combos),
        "zero_evidence_examples": missing_combos[:50],
    }

    with open("output/ayurveda_kb_structured.json", "w", encoding="utf-8") as f:
        json.dump(structured, f, indent=2, ensure_ascii=False)
    with open("output/ayurveda_kb_flat.json", "w", encoding="utf-8") as f:
        json.dump(flat, f, indent=2, ensure_ascii=False)
    with open("output/ayurveda_kb_final.json", "w", encoding="utf-8") as f:
        json.dump(flat, f, indent=2, ensure_ascii=False)
    with open("output/kb_quality_report.json", "w", encoding="utf-8") as f:
        json.dump(quality, f, indent=2, ensure_ascii=False)

    # Keep a stable source-of-truth artifact for manual curation.
    medicine_master = {
        disease: [
            {
                "medicine_name": details["medicine_name"],
                "formulation_type": details["formulation_type"],
                "herb_sanskrit": details["herb_sanskrit"],
                "dosha_type": details["dosha_type"],
                "dosage": "Standard protocol - twice daily after meals",
                "allowed_ages": ["all"],
                "allowed_genders": ["all"],
                "allowed_severities": ["low", "medium", "high"],
                "child_safe": details["constraints"]["child_safe"],
                "elderly_safe": details["constraints"]["elderly_safe"],
                "pregnant_safe": details["constraints"]["pregnant_safe"],
            }
        ]
        for disease, details in master.items()
    }
    with open("medicine_master.json", "w", encoding="utf-8") as f:
        json.dump(medicine_master, f, indent=2, ensure_ascii=False)

    print(f"Diseases covered: {quality['disease_count']}")
    print(f"Dataset records: {quality['total_records']}")
    print("Saved: output/ayurveda_kb_structured.json")
    print("Saved: output/ayurveda_kb_final.json")
    print("Saved: output/kb_quality_report.json")
    print("Saved: medicine_master.json\n")
    return structured


if __name__ == "__main__":
    run()