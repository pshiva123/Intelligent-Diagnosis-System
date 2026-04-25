import json
import re
from pathlib import Path

from pipeline_config import DISEASES, DOSHA_HINTS, HERB_HINTS
from text_utils import sentence_split


def detect_dosha(sentence: str) -> str:
    scores = {}
    low = sentence.lower()
    for dosha, hints in DOSHA_HINTS.items():
        scores[dosha] = sum(1 for h in hints if h in low)
    return max(scores, key=scores.get) if any(scores.values()) else "tridosha"


def detect_severity(sentence: str) -> str:
    low = sentence.lower()
    if re.search(r"\b(severe|acute|critical|intense|advanced)\b", low):
        return "high"
    if re.search(r"\b(mild|slight|early)\b", low):
        return "low"
    return "medium"


def detect_constraints(sentence: str) -> dict:
    low = sentence.lower()
    return {
        "child_safe": not bool(re.search(r"(not|avoid|contraindicated).{0,20}(child|children|infant)", low)),
        "elderly_safe": not bool(re.search(r"(avoid|caution).{0,20}(elder|elderly)", low)),
        "pregnant_safe": not bool(re.search(r"(avoid|not|contraindicated).{0,20}(pregnan)", low)),
    }


def extract_herbs_rule_based(sentence: str) -> list[str]:
    low = sentence.lower()
    found = []
    for herb in HERB_HINTS:
        if re.search(rf"\b{re.escape(herb)}\b", low):
            found.append(herb)
    return found


def init_biomedical_ner():
    try:
        import torch
        from transformers import AutoModelForTokenClassification, AutoTokenizer, pipeline

        model_id = "d4data/biomedical-ner-all"
        device = 0 if torch.cuda.is_available() else -1
        ner_pipeline = pipeline(
            "ner",
            model=AutoModelForTokenClassification.from_pretrained(model_id),
            tokenizer=AutoTokenizer.from_pretrained(model_id),
            aggregation_strategy="max",
            device=device,
        )
        print(f"  OK: biomedical NER loaded ({'GPU' if torch.cuda.is_available() else 'CPU'})")
        return ner_pipeline
    except Exception as exc:
        print(f"  WARN: biomedical NER unavailable ({exc}). Falling back to rules.")
        return None


def extract_herbs_biomedical(sentence: str, ner_pipeline) -> list[str]:
    if ner_pipeline is None:
        return []
    try:
        entities = ner_pipeline(sentence[:2000])
    except Exception:
        return []
    herbs = []
    for ent in entities:
        word = str(ent.get("word", "")).strip().lower()
        score = float(ent.get("score", 0.0))
        if score >= 0.65 and len(word) >= 3 and word.isascii():
            herbs.append(word)
    return herbs


def extract_disease_mentions(sentence: str) -> list[str]:
    low = sentence.lower()
    return [d for d in DISEASES if d.lower() in low]


def run():
    print("=" * 65)
    print("STEP 2 - NLP Knowledge Extraction")
    print("=" * 65)

    corpus_path = Path("scraped_texts/raw_corpus.json")
    if not corpus_path.exists():
        print("  ERROR: Run step1_scrapper.py first.")
        return []

    corpus = json.load(open(corpus_path, encoding="utf-8"))
    Path("extracted_data").mkdir(exist_ok=True)
    ner_pipeline = init_biomedical_ner()

    extracted = []
    for doc in corpus:
        text = doc.get("text", "")
        for sentence in sentence_split(text):
            diseases = extract_disease_mentions(sentence)
            if not diseases:
                continue

            herbs_rb = extract_herbs_rule_based(sentence)
            herbs_ner = extract_herbs_biomedical(sentence, ner_pipeline)
            herbs = sorted(set(herbs_rb + herbs_ner))
            if not herbs:
                continue

            item = {
                "source_label": doc.get("label"),
                "source_url": doc.get("url"),
                "source_category": doc.get("category"),
                "evidence_text": sentence,
                "diseases": diseases,
                "herbs_found": herbs,
                "dosha_type": detect_dosha(sentence),
                "severity": detect_severity(sentence),
                "constraints": detect_constraints(sentence),
                "confidence_score": round(min(0.99, 0.55 + 0.08 * len(herbs)), 3),
            }
            extracted.append(item)

    output_path = Path("extracted_data/biobert_extractions.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(extracted, f, indent=2, ensure_ascii=False)

    print(f"Extracted relations: {len(extracted)}")
    print(f"Saved extractions: {output_path.as_posix()}\n")
    return extracted


if __name__ == "__main__":
    run()