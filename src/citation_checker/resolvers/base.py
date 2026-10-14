from typing import Protocol

from citation_checker.models import Candidate


class Resolver(Protocol):
    name: str

    async def lookup(self, doi: str) -> Candidate | None:
        """Fetch the record for a DOI; None if this source doesn't know it."""
        ...

    async def search(self, citation: str, rows: int = 5) -> list[Candidate]:
        """Search by free-text citation; best candidates first."""
        ...
