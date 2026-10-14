import asyncio
import json
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table

from citation_checker.models import Verdict
from citation_checker.pipeline import check_many

app = typer.Typer(add_completion=False, help="Check that citations actually exist.")

STYLE = {
    Verdict.VERIFIED: "green",
    Verdict.VERIFIED_WITH_DISCREPANCIES: "yellow",
    Verdict.NEEDS_REVIEW: "yellow",
    Verdict.MISATTRIBUTED: "red",
    Verdict.NOT_FOUND: "red",
}
FAILING = {Verdict.MISATTRIBUTED, Verdict.NOT_FOUND}


@app.callback()
def _root() -> None:
    """Check that citations actually exist."""


def read_citations(path: Path) -> list[str]:
    """One citation per non-empty line."""
    return [line.strip() for line in path.read_text().splitlines() if line.strip()]


@app.command()
def check(
    citations: Annotated[
        list[str] | None, typer.Argument(help="Citation strings.")
    ] = None,
    file: Annotated[
        Path | None,
        typer.Option(
            "--file", "-f", exists=True, help="Text file, one citation per line."
        ),
    ] = None,
    as_json: Annotated[
        bool, typer.Option("--json", help="Emit JSON instead of a table.")
    ] = False,
    mailto: Annotated[
        str | None,
        typer.Option(
            envvar="CITATION_CHECKER_EMAIL",
            help="Contact email for Crossref's polite pool.",
        ),
    ] = None,
) -> None:
    """Check citations; exits 1 if any are not found or misattributed."""
    items = list(citations or [])
    if file:
        items += read_citations(file)
    if not items:
        raise typer.BadParameter("give citations as arguments or with --file")

    results = asyncio.run(check_many(items, mailto=mailto))

    if as_json:
        typer.echo(json.dumps([r.model_dump(mode="json") for r in results], indent=2))
    else:
        table = Table(show_lines=True)
        for col in ("Citation", "Verdict", "Score", "Matched record", "Notes"):
            table.add_column(col, overflow="fold")
        for r in results:
            rec = ""
            if r.match:
                authors = ", ".join(r.match.authors[:3])
                rec = f"{r.match.title}\n{authors} ({r.match.year})\n{r.match.doi}"
            notes = "; ".join(
                filter(None, [r.note, *(r.score.discrepancies if r.score else [])])
            )
            table.add_row(
                r.citation,
                f"[{STYLE[r.verdict]}]{r.verdict.value}[/]",
                f"{r.score.total:.2f}" if r.score else "",
                rec,
                notes,
            )
        Console().print(table)

    raise typer.Exit(1 if any(r.verdict in FAILING for r in results) else 0)
