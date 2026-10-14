# citation-checker

Check that citations, in any format, refer to works that actually exist.

Prototype: Crossref only, deterministic fuzzy matching. Existence is always grounded
in an external record, never in a model's opinion.

## Usage

```sh
uv run citation-checker check "Harris, C. R., et al. (2020). Array programming with NumPy. Nature."
uv run citation-checker check -f refs.bib          # BibTeX; results keyed by entry
uv run citation-checker check -f refs.txt          # one citation per line
uv run citation-checker check -f refs.txt --json   # machine-readable output
```

Set `CITATION_CHECKER_EMAIL` (or `--mailto`) to use Crossref's polite pool, which
allows more concurrent requests. Exit status is 1 if any citation is `not_found` or
`misattributed`.

## Verdicts

| Verdict | Meaning |
| --- | --- |
| `verified` | Matching record found, metadata agrees |
| `verified_with_discrepancies` | Work exists; year/authors differ |
| `misattributed` | DOI resolves, but to a different work |
| `not_found` | DOI doesn't resolve, or no credible search match |
| `needs_review` | Ambiguous match, non-Crossref DOI, or lookup failure |

## Layout

- `ingest.py` – read `.bib` (bibtexparser) or plain-text citation files
- `identifiers.py` – DOI extraction
- `resolvers/` – `Resolver` protocol; Crossref implementation
- `match.py` – fuzzy scoring of a raw citation against a candidate record
- `pipeline.py` – async `check` / `check_many` (the API a web app would call)
- `cli.py` – typer CLI
