from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class Verdict(str, Enum):
    VERIFIED = "verified"
    VERIFIED_WITH_DISCREPANCIES = "verified_with_discrepancies"
    MISATTRIBUTED = "misattributed"  # identifier resolves, but to a different work
    NOT_FOUND = "not_found"
    NEEDS_REVIEW = "needs_review"


class RawCitation(BaseModel):
    """A citation as given by the user, before any lookup."""

    text: str
    key: str | None = None  # e.g. a BibTeX key


class Candidate(BaseModel):
    """A bibliographic record returned by an external source."""

    source: str
    doi: str | None = None
    title: str | None = None
    authors: list[str] = Field(default_factory=list)  # family names
    year: int | None = None
    container: str | None = None
    url: str | None = None


class MatchScore(BaseModel):
    title: float
    authors: float
    year: float
    total: float
    discrepancies: list[str] = Field(default_factory=list)


class CheckResult(BaseModel):
    citation: str
    key: str | None = None
    verdict: Verdict
    doi_in_citation: str | None = None
    match: Candidate | None = None
    score: MatchScore | None = None
    note: str | None = None
