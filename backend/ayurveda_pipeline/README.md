# Ayurveda KB Dataset Pipeline

This pipeline builds a structured Ayurvedic dataset using source priority:

1. Classical texts (Charaka / Sushruta web sources)
2. Government Ayurveda portals
3. Google fallback search (only when disease coverage is missing)

## Run

```bash
python run_all.py
```

Or run individual steps:

```bash
python step1_scrapper.py
python step2_biobert_extractor.py
python step3_build_kb.py
```

## Output Files

- `scraped_texts/raw_corpus.json`
- `scraped_texts/coverage_report.json`
- `extracted_data/biobert_extractions.json`
- `output/ayurveda_kb_structured.json`
- `output/ayurveda_kb_final.json`
- `output/kb_quality_report.json`
- `medicine_master.json`

## Notes

- `medicine_master.json` is generated and can be manually curated to improve quality.
- Step 2 uses biomedical NER if available; otherwise it falls back to deterministic rule extraction.
- `output/ayurveda_kb_structured.json` is the file used by backend inference.
