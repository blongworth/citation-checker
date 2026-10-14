import asyncio

import httpx

from citation_checker.identifiers import extract_doi
from citation_checker.match import score
from citation_checker.models import CheckResult, RawCitation, Verdict
from citation_checker.resolvers.crossref import (
    POLITE_CONCURRENCY,
    PUBLIC_CONCURRENCY,
    CrossrefResolver,
    doi_registered,
)

ACCEPT = 0.85  # total score for VERIFIED
TITLE_OK = 0.9  # title match strong enough to say the work exists
REVIEW = 0.6  # below this a search hit is treated as no match


def _judge(total: float, title: float, discrepancies: list[str]) -> Verdict:
    if total >= ACCEPT and not discrepancies:
        return Verdict.VERIFIED
    if title >= TITLE_OK:
        return Verdict.VERIFIED_WITH_DISCREPANCIES
    if total >= REVIEW:
        return Verdict.NEEDS_REVIEW
    return Verdict.NOT_FOUND


async def check(
    citation: str, client: httpx.AsyncClient, mailto: str | None = None
) -> CheckResult:
    crossref = CrossrefResolver(client, mailto)
    doi = extract_doi(citation)

    if doi:
        cand = await crossref.lookup(doi)
        if cand is None:
            if await doi_registered(client, doi):
                return CheckResult(
                    citation=citation,
                    verdict=Verdict.NEEDS_REVIEW,
                    doi_in_citation=doi,
                    note="DOI is registered outside Crossref; metadata not checked",
                )
            return CheckResult(
                citation=citation,
                verdict=Verdict.NOT_FOUND,
                doi_in_citation=doi,
                note="DOI does not resolve",
            )
        s = score(citation, cand)
        verdict = _judge(s.total, s.title, s.discrepancies)
        if verdict in (Verdict.NEEDS_REVIEW, Verdict.NOT_FOUND):
            verdict = Verdict.MISATTRIBUTED
        return CheckResult(
            citation=citation, verdict=verdict, doi_in_citation=doi, match=cand, score=s
        )

    candidates = await crossref.search(citation)
    if not candidates:
        return CheckResult(
            citation=citation, verdict=Verdict.NOT_FOUND, note="no search results"
        )
    best, s = max(
        ((c, score(citation, c)) for c in candidates), key=lambda cs: cs[1].total
    )
    verdict = _judge(s.total, s.title, s.discrepancies)
    return CheckResult(
        citation=citation,
        verdict=verdict,
        match=best if verdict != Verdict.NOT_FOUND else None,
        score=s,
        note="closest record is not a match" if verdict == Verdict.NOT_FOUND else None,
    )


async def check_many(
    citations: list[str | RawCitation],
    mailto: str | None = None,
    concurrency: int | None = None,
) -> list[CheckResult]:
    if concurrency is None:
        concurrency = POLITE_CONCURRENCY if mailto else PUBLIC_CONCURRENCY
    sem = asyncio.Semaphore(concurrency)
    headers = {"User-Agent": "citation-checker/0.1"}
    async with httpx.AsyncClient(
        timeout=30, headers=headers, follow_redirects=True
    ) as client:

        async def one(c: str | RawCitation) -> CheckResult:
            if isinstance(c, str):
                c = RawCitation(text=c)
            async with sem:
                try:
                    result = await check(c.text, client, mailto)
                except httpx.HTTPError as e:
                    result = CheckResult(
                        citation=c.text,
                        verdict=Verdict.NEEDS_REVIEW,
                        note=f"lookup failed: {type(e).__name__}: {e}".splitlines()[0],
                    )
            result.key = c.key
            return result

        return await asyncio.gather(*(one(c) for c in citations))
