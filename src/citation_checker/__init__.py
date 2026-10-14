"""Check that citations refer to works that actually exist."""

from citation_checker.models import CheckResult, Verdict
from citation_checker.pipeline import check, check_many

__all__ = ["CheckResult", "Verdict", "check", "check_many", "main"]


def main() -> None:
    from citation_checker.cli import app

    app()
