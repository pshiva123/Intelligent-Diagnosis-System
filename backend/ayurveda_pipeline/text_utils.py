import re
from typing import Iterable

import trafilatura
from bs4 import BeautifulSoup


def clean_text(raw_html: str) -> str:
    extracted = trafilatura.extract(raw_html, include_comments=False, include_tables=False)
    if extracted:
        return normalize_whitespace(extracted)

    soup = BeautifulSoup(raw_html, "lxml")
    for tag in soup(["script", "style", "nav", "footer", "aside"]):
        tag.decompose()
    text = soup.get_text(separator=" ")
    return normalize_whitespace(text)


def normalize_whitespace(text: str) -> str:
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def sentence_split(text: str) -> list[str]:
    chunks = re.split(r"(?<=[.!?])\s+", text)
    return [c.strip() for c in chunks if len(c.strip()) > 20]


def contains_any(text: str, tokens: Iterable[str]) -> bool:
    lower = text.lower()
    return any(t.lower() in lower for t in tokens)

