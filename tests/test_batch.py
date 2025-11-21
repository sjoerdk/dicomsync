import logging
from unittest.mock import Mock, patch

from dicomsync.batch import send_studies, group_results
from dicomsync.core import AssertionStatus
from dicomsync.exceptions import DICOMSyncTimeoutError, StudyAlreadyExistsError
from dicomsync.xnat import XNATProjectPreArchive
from tests.factories import (
    XNATProjectPreArchiveFactory,
    ZippedDICOMRootFolderFactory,
    ZippedDICOMStudyFactory,
)


def test_switchboard(caplog):
    """Try different things that can go wrong while sending a list of studies to a
    location
    """
    caplog.set_level(logging.INFO)

    # I want to send zipped studies to XNAT
    source_place = ZippedDICOMRootFolderFactory()
    studies = [
        ZippedDICOMStudyFactory(place=source_place),
        ZippedDICOMStudyFactory(place=source_place),
        ZippedDICOMStudyFactory(place=source_place),
    ]
    destination_place = XNATProjectPreArchiveFactory()

    # Sending a zipped study to this destination will time out the first call, sadly
    # but after that will be fine

    # a mock that will raise exception, then pass, then raise a different exception.
    # Patching the class here because pydantic does not allow access to __slots__ for
    # BaseModels
    with patch.object(
        XNATProjectPreArchive,
        "send_zipped_study",
        Mock(
            side_effect=[
                DICOMSyncTimeoutError("Too slow!"),
                None,
                StudyAlreadyExistsError("Already there!"),
            ]
        ),
    ):
        results = send_studies(studies, place=destination_place)

    grouped = group_results(results)

    # two jobs should have failed
    assert len(grouped[AssertionStatus.error]) == 2
    # one job should have succeeded
    assert len(grouped[AssertionStatus.created]) == 1
