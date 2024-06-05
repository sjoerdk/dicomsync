from dicomsync.core import AssertionResult, AssertionStatus
from dicomsync.ui import summarize_results


def test_summarize_results():
    summary = summarize_results(
        [
            AssertionResult(status=AssertionStatus.skipped),
            AssertionResult(status=AssertionStatus.skipped),
            AssertionResult(status=AssertionStatus.created),
            AssertionResult(status=AssertionStatus.error, message="Terrible problem"),
            AssertionResult(status=AssertionStatus.not_set),
        ]
    )
    assert "skipped: 2" in summary
