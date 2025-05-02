import fnmatch
from typing import Dict, List, Union

import click
from tabulate import tabulate

from dicomsync.cli.base import DicomSyncContext, dicom_sync_command
from dicomsync.cli.click_parameter_types import QueryParameterType
from dicomsync.core import Place
from dicomsync.references import StudyKey, StudyQuery, StudyURI
from dicomsync.logs import get_module_logger

logger = get_module_logger("cli.find")


@dicom_sync_command(name="find")
@click.argument("query", type=QueryParameterType())
def find(context: DicomSyncContext, query: Union[StudyQuery, str]):
    """Find DICOM studies in places"""

    # get current places
    settings = context.load_settings()
    if isinstance(query, StudyQuery):
        # user is asking for studies
        study_uris = perform_study_query(places=settings.places, study_query=query)
        click.echo(
            f"found {len(study_uris)}:\n" + "\n".join(list(map(str, study_uris)))
        )

    elif isinstance(query, str):
        places = perform_place_query(places=settings.places, place_query=query)
        table = []
        for key, place in places.items():
            table.append({"key": key, "place": str(place)})
        click.echo(tabulate(table, headers="keys"))


def perform_study_query(
    places: Dict[str, Place], study_query: StudyQuery
) -> List[StudyURI]:
    """Find all studies in places that match query"""

    found = []
    matching_places = perform_place_query(
        places=places, place_query=study_query.place_pattern
    )
    for place_name, place in matching_places.items():
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


def perform_place_query(places: Dict[str, Place], place_query: str) -> Dict[str, Place]:
    """Find all places matching query"""

    matching = [x for x in fnmatch.filter(places.keys(), place_query)]
    return {x: places[x] for x in matching}
