import re

# Crossref's recommended pattern, loosened to stop at whitespace.
_DOI_RE = re.compile(r"\b(10\.\d{4,9}/[^\s\"<>]+)", re.IGNORECASE)


def extract_doi(text: str) -> str | None:
    """Return the first DOI in `text`, without trailing punctuation."""
    m = _DOI_RE.search(text)
    if not m:
        return None
    return m.group(1).rstrip(".,;)]}").lower()
