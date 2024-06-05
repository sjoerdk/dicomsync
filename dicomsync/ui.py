"""Miscellaneous functions to show things more neatly"""
from collections import Counter
from typing import List

from dicomsync.core import AssertionResult


def summarize_results(assertion_results: List[AssertionResult]):
    counter = Counter(x.status for x in assertion_results)
    results = [x[0].name + ": " + str(x[1]) for x in counter.items()]
    return f"Processed {len(assertion_results)} results - {', '.join(results)}"
