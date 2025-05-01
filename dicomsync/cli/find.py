import fnmatch
from typing import Dict

import click

from dicomsync.cli.base import DicomSyncContext, dicom_sync_command
from dicomsync.cli.click_parameter_types import StudyQueryParameterType
from dicomsync.core import Place
from dicomsync.references import StudyKey, StudyQuery, StudyURI
from dicomsync.logs import get_module_logger

logger = get_module_logger("cli.find")


@dicom_sync_command(name="find")
@click.argument("study_uri_query", type=StudyQueryParameterType())
def find(context: DicomSyncContext, study_uri_query: StudyQuery):
    """Find DICOM studies in places"""

    # get current places
    settings = context.load_settings()
    found = perform_query(places=settings.places, study_query=study_uri_query)

    print(f"found {len(found)}:\n" + "\n".join(list(map(str, found))))


def perform_query(places: Dict[str, Place], study_query: StudyQuery):
    """Find all studies in places that match query

    Returns
    -------
    List[StudyURI]
    """

    found = []
    matching_place_names = [
        x for x in fnmatch.filter(places.keys(), study_query.place_pattern)
    ]
    for place_name in matching_place_names:
        place = places[place_name]
        found_keys = fnmatch.filter(
            (str(x.key()) for x in place.all_studies()), study_query.key_pattern
        )
        for key in found_keys:
            found.append(
                StudyURI(
                    place_name=place_name, study_key=StudyKey.init_from_string(key)
                )
            )

    return found
