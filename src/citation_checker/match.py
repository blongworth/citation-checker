"""Deterministic fuzzy matching of a raw citation string against a candidate record.

No parsing is needed: we check whether the candidate's fields appear in the raw text.
"""

import re
import unicodedata

from rapidfuzz import fuzz

from citation_checker.models import Candidate, MatchScore

WEIGHTS = {"title": 0.6, "authors": 0.25, "year": 0.15}


def normalize(text: str) -> str:
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    text = re.sub(r"<[^>]+>", " ", text)  # Crossref titles can contain markup
    text = re.sub(r"[^\w\s]", " ", text.lower())
    return re.sub(r"\s+", " ", text).strip()


def score(citation: str, cand: Candidate) -> MatchScore:
    raw = normalize(citation)
    tokens = set(raw.split())
    discrepancies = []

    title = 0.0
    if cand.title:
        title = fuzz.partial_ratio(normalize(cand.title), raw) / 100
        if title < 0.9:
            discrepancies.append("title differs")

    authors = 0.0
    names = [normalize(a) for a in cand.authors[:5]]
    if names:
        hits = sum(all(p in tokens for p in n.split()) for n in names)
        authors = hits / len(names)
        if authors < 0.5:
            discrepancies.append("authors not found in citation")

    year = 0.0
    years = {int(y) for y in re.findall(r"\b(1[5-9]\d\d|20\d\d)\b", raw)}
    if cand.year and years:
        if cand.year in years:
            year = 1.0
        elif any(abs(cand.year - y) <= 1 for y in years):
            year = 0.5
            discrepancies.append(f"year off by one (record: {cand.year})")
        else:
            discrepancies.append(f"year mismatch (record: {cand.year})")

    total = sum(
        WEIGHTS[k] * v
        for k, v in {"title": title, "authors": authors, "year": year}.items()
    )
    return MatchScore(
        title=title,
        authors=authors,
        year=year,
        total=round(total, 3),
        discrepancies=discrepancies,
    )
