"""Functions and classes for processing multiple studies at once.
Separate module because I don't want to fold this functionality in with CLI and I want
to test it separately.
"""
from collections import defaultdict
from typing import Any, Dict, List

from dicomsync.core import AssertionResult, AssertionStatus, ImagingStudy, Place
from dicomsync.exceptions import DICOMSyncError
from dicomsync.logs import get_module_logger
from dicomsync.routing import SwitchBoard

logger = get_module_logger("batch")


def send_studies(
    studies: List[ImagingStudy[Any]], place: Place[Any], dry_run: bool = False
):
    """Send studies to place, handle exceptions.

    Returns
    -------
    Dict[Study, AssertionResult]

    """
    to_send = "\n".join([str(x) for x in studies])
    logger.debug(f"Sending the following studies to {place}: {to_send}")

    results = {}
    board = SwitchBoard()
    for idx, study in enumerate(studies, start=1):
        logger.info(f"processing ({idx} of {len(studies)}):{study}")
        try:
            board.send(study=study, place=place, dry_run=dry_run)
            results[study] = AssertionResult(status=AssertionStatus.created)
        except DICOMSyncError as e:
            logger.error(f"Error sending {study}: {e}")
            logger.info(f"skipping {study} due to error")
            results[study] = AssertionResult(
                status=AssertionStatus.error, message=str(e)
            )
            continue

    return results


def group_results(assertion_results: Dict[ImagingStudy[Any], AssertionResult]):
    """Sort results by type: error, succeded etc. This loses specifics about errors and
    just summarises.
    """
    grouped = defaultdict(list)
    for study, result in assertion_results.items():
        grouped[result.status].append(study)
    return dict(grouped)


def summarize_results(
    assertion_results: Dict[ImagingStudy[Any], AssertionResult]
) -> str:
    grouped = group_results(assertion_results)
    results = [
        str(status) + ": " + str(len(studies)) for status, studies in grouped.items()
    ]
    return f"Processed {len(assertion_results)} results - {', '.join(results)}"
