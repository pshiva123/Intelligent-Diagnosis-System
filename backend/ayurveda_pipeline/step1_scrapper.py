import json
import time
from pathlib import Path
from urllib.parse import quote, urlparse

import requests
from bs4 import BeautifulSoup

from pipeline_config import CLASSICAL_SOURCES, DISEASES, GOVERNMENT_SOURCES
from text_utils import clean_text, contains_any

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept-Language": "en-US,en;q=0.9",
}


def fetch_page(url: str, timeout: int = 25) -> str:
    response = requests.get(url, headers=HEADERS, timeout=timeout)
    response.raise_for_status()
    return response.text


def scrape_source(label: str, url: str, category: str, max_chars: int = 30000) -> dict | None:
    try:
        raw_html = fetch_page(url)
        text = clean_text(raw_html)
        if len(text) < 500:
            return None
        return {
            "label": label,
            "url": url,
            "domain": urlparse(url).netloc,
            "category": category,
            "text": text[:max_chars],
            "chars": len(text),
        }
    except Exception:
        return None


def google_search_urls(query: str, max_results: int = 5) -> list[str]:
    search_url = f"https://www.google.com/search?q={quote(query)}"
    html = fetch_page(search_url, timeout=20)
    soup = BeautifulSoup(html, "lxml")
    urls = []
    for anchor in soup.select("a[href]"):
        href = anchor.get("href", "")
        if href.startswith("/url?q="):
            target = href.split("/url?q=")[1].split("&")[0]
            if target.startswith("http") and "google.com" not in target:
                urls.append(target)
        if len(urls) >= max_results:
            break
    return urls


def collect_priority_sources() -> list[dict]:
    docs = []
    for src in [*CLASSICAL_SOURCES, *GOVERNMENT_SOURCES]:
        item = scrape_source(src.label, src.url, src.category)
        if item:
            docs.append(item)
        time.sleep(1)
    return docs


def has_disease_coverage(docs: list[dict], disease: str) -> bool:
    for doc in docs:
        if contains_any(doc["text"], [disease, disease.lower()]):
            return True
    return False


def collect_google_fallback(docs: list[dict]) -> list[dict]:
    fetched_urls = {d["url"] for d in docs}
    additions = []
    for disease in DISEASES:
        if has_disease_coverage(docs + additions, disease):
            continue
        query = f"{disease} ayurveda treatment site:gov.in OR site:org"
        try:
            candidates = google_search_urls(query, max_results=5)
        except Exception:
            candidates = []
        for url in candidates:
            if url in fetched_urls:
                continue
            fetched_urls.add(url)
            item = scrape_source(f"GoogleFallback-{disease}", url, "google_fallback")
            if item:
                item["disease_hint"] = disease
                additions.append(item)
            time.sleep(1)
    return additions


def run():
    print("=" * 65)
    print("STEP 1 - Multi-source Ayurvedic Corpus Collection")
    print("=" * 65)
    print("Priority: Classical texts -> Government portals -> Google fallback")

    Path("scraped_texts").mkdir(exist_ok=True)

    base_docs = collect_priority_sources()
    fallback_docs = collect_google_fallback(base_docs)
    corpus = base_docs + fallback_docs

    out_path = Path("scraped_texts/raw_corpus.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(corpus, f, indent=2, ensure_ascii=False)

    coverage = {}
    for disease in DISEASES:
        coverage[disease] = has_disease_coverage(corpus, disease)

    coverage_path = Path("scraped_texts/coverage_report.json")
    with open(coverage_path, "w", encoding="utf-8") as f:
        json.dump(coverage, f, indent=2, ensure_ascii=False)

    total_chars = sum(d["chars"] for d in corpus)
    print(f"\nCollected docs: {len(corpus)}")
    print(f"Total text size: {total_chars:,} chars")
    print(f"Saved corpus: {out_path.as_posix()}")
    print(f"Saved coverage report: {coverage_path.as_posix()}\n")
    return corpus


if __name__ == "__main__":
    run()