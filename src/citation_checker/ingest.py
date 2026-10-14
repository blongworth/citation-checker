"""Read citations from files. Dispatches on file extension."""

import re
from pathlib import Path

import bibtexparser
from bibtexparser.middlewares import LatexDecodingMiddleware, SeparateCoAuthors

from citation_checker.models import RawCitation

_MATH_RE = re.compile(r"\$([^$]*)\$")


def _clean(value: str) -> str:
    """Flatten leftover LaTeX math (e.g. N$_2$, $^{15}$N) and whitespace."""
    value = _MATH_RE.sub(lambda m: re.sub(r"[_^{}\\]", "", m.group(1)), value)
    return re.sub(r"\s+", " ", value.replace("{", "").replace("}", "")).strip()


def _bib_entry_text(fields: dict) -> str:
    """Render a BibTeX entry as a plain citation string the matcher can score."""
    authors = fields.get("author") or fields.get("editor") or []
    if isinstance(authors, str):
        authors = [authors]
    venue = next(
        (
            fields[k]
            for k in ("journal", "booktitle", "publisher", "howpublished", "school")
            if k in fields
        ),
        "",
    )
    parts = [
        f"{'; '.join(authors)} ({fields.get('year', 'n.d.')}).",
        f"{fields.get('title', '')}.",
        ", ".join(filter(None, [venue, fields.get("volume"), fields.get("pages")])),
    ]
    if fields.get("doi"):
        parts.append(f"https://doi.org/{fields['doi']}")
    elif fields.get("url"):
        parts.append(fields["url"])
    return _clean(" ".join(p for p in parts if p))


def read_bib(path: Path) -> list[RawCitation]:
    library = bibtexparser.parse_file(
        str(path), append_middleware=[LatexDecodingMiddleware(), SeparateCoAuthors()]
    )
    if library.failed_blocks:
        raise ValueError(
            f"{path}: {len(library.failed_blocks)} BibTeX block(s) could not be parsed"
        )
    return [
        RawCitation(
            key=e.key,
            text=_bib_entry_text({f.key.lower(): f.value for f in e.fields}),
        )
        for e in library.entries
    ]


def read_lines(path: Path) -> list[RawCitation]:
    """One citation per non-empty line."""
    return [
        RawCitation(text=line.strip())
        for line in path.read_text().splitlines()
        if line.strip()
    ]


def read_citations(path: Path) -> list[RawCitation]:
    if path.suffix.lower() == ".bib":
        return read_bib(path)
    return read_lines(path)
