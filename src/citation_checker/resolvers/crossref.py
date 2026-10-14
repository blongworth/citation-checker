import asyncio

import httpx

from citation_checker.models import Candidate

API = "https://api.crossref.org"
# Crossref's documented concurrency limits for the public and polite pools.
PUBLIC_CONCURRENCY = 1
POLITE_CONCURRENCY = 3


async def get_with_retry(
    client: httpx.AsyncClient, url: str, retries: int = 3, **kwargs
) -> httpx.Response:
    """GET, backing off on 429/503 using Retry-After when given."""
    for attempt in range(retries + 1):
        r = await client.get(url, **kwargs)
        if r.status_code not in (429, 503) or attempt == retries:
            return r
        await asyncio.sleep(float(r.headers.get("Retry-After", 2**attempt)))
    return r


def _to_candidate(item: dict) -> Candidate:
    year = None
    for key in ("issued", "published-print", "published-online", "created"):
        parts = item.get(key, {}).get("date-parts", [[None]])
        if parts and parts[0] and parts[0][0]:
            year = int(parts[0][0])
            break
    return Candidate(
        source="crossref",
        doi=item.get("DOI", "").lower() or None,
        title=(item.get("title") or [None])[0],
        authors=[a["family"] for a in item.get("author", []) if "family" in a],
        year=year,
        container=(item.get("container-title") or [None])[0],
        url=item.get("URL"),
    )


class CrossrefResolver:
    name = "crossref"

    def __init__(self, client: httpx.AsyncClient, mailto: str | None = None):
        self.client = client
        # Supplying a contact email puts requests in Crossref's "polite" pool.
        self.params = {"mailto": mailto} if mailto else {}

    async def lookup(self, doi: str) -> Candidate | None:
        r = await get_with_retry(self.client, f"{API}/works/{doi}", params=self.params)
        if r.status_code == 404:
            return None
        r.raise_for_status()
        return _to_candidate(r.json()["message"])

    async def search(self, citation: str, rows: int = 5) -> list[Candidate]:
        params = {**self.params, "query.bibliographic": citation, "rows": rows}
        r = await get_with_retry(self.client, f"{API}/works", params=params)
        r.raise_for_status()
        return [_to_candidate(i) for i in r.json()["message"]["items"]]


async def doi_registered(client: httpx.AsyncClient, doi: str) -> bool:
    """Whether a DOI exists with any registration agency (DataCite, mEDRA, ...)."""
    r = await client.get(f"https://doi.org/api/handles/{doi}")
    return r.status_code == 200 and r.json().get("responseCode") == 1
