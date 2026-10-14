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
