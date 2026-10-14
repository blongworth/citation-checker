from citation_checker.identifiers import extract_doi
from citation_checker.match import score
from citation_checker.models import Candidate, Verdict
from citation_checker.pipeline import _judge

CAND = Candidate(
    source="test",
    title="Array programming with NumPy",
    authors=["Harris", "Millman", "van der Walt"],
    year=2020,
)


def test_extract_doi():
    assert (
        extract_doi(
            "Nature 585, 357 (2020). https://doi.org/10.1038/S41586-020-2649-2."
        )
        == "10.1038/s41586-020-2649-2"
    )
    assert extract_doi("no identifier here") is None


def test_score_exact():
    s = score(
        "Harris, C. R., Millman, K. J., van der Walt, S. J. (2020). "
        "Array programming with NumPy. Nature.",
        CAND,
    )
    assert s.total > 0.95 and not s.discrepancies
    assert _judge(s.total, s.title, s.discrepancies) == Verdict.VERIFIED


def test_score_wrong_year():
    s = score("Harris, Millman, van der Walt (2015) Array programming with NumPy", CAND)
    assert s.title > 0.9 and s.year == 0
    assert (
        _judge(s.total, s.title, s.discrepancies) == Verdict.VERIFIED_WITH_DISCREPANCIES
    )


def test_score_different_work():
    s = score("Smith, J. (2020). Deep learning for ocean acidification.", CAND)
    assert _judge(s.total, s.title, s.discrepancies) == Verdict.NOT_FOUND


BIB = r"""
@article{eyre2013,
  author  = {Eyre, Bradley D. and Santos, Isaac R. and Maher, Damien T.},
  title   = {Seasonal, daily and diel {N}$_2$ effluxes in permeable carbonate
             sediments},
  journal = {Biogeosciences},
  year    = {2013},
  volume  = {10},
  pages   = {2601--2615},
  doi     = {10.5194/bg-10-2601-2013}
}

@misc{schlueter2008,
  author = {Schl{\"u}ter, Michael},
  title  = {Methane in aquatic environments},
  year   = {2008}
}
"""


def test_read_bib(tmp_path):
    from citation_checker.ingest import read_citations

    path = tmp_path / "refs.bib"
    path.write_text(BIB)
    eyre, schlueter = read_citations(path)
    assert eyre.key == "eyre2013"
    assert eyre.text == (
        "Eyre, Bradley D.; Santos, Isaac R.; Maher, Damien T. (2013). "
        "Seasonal, daily and diel N2 effluxes in permeable carbonate sediments. "
        "Biogeosciences, 10, 2601–2615 https://doi.org/10.5194/bg-10-2601-2013"
    )
    assert extract_doi(eyre.text) == "10.5194/bg-10-2601-2013"
    assert schlueter.text.startswith("Schlüter, Michael (2008).")
