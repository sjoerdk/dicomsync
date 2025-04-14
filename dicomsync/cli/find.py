import fnmatch

import click

from dicomsync.cli.base import DicomSyncContext, dicom_sync_command
from dicomsync.cli.click_parameter_types import StudyURIQueryParameterType
from dicomsync.core import StudyURI
from dicomsync.logs import get_module_logger

logger = get_module_logger("cli.find")


@dicom_sync_command(name="find")
@click.argument("study_uri_query", type=StudyURIQueryParameterType())
def find(context: DicomSyncContext, study_uri_query: StudyURI):
    """Find DICOM studies in places"""

    click.echo(f"find {study_uri_query}")

    # get current places
    settings = context.load_settings()
    found = []
    for place_name in fnmatch.filter(
        settings.places.keys(), study_uri_query.place_name
    ):
        for study in settings.places[place_name].all_studies():

            if fnmatch.fnmatch(
                study.subject.name, study_uri_query.patient.name
            ) and fnmatch.fnmatch(study.description, study_uri_query.study_key):
                found.append(
                    StudyURI(
                        place_name=place_name,
                        patient=study.subject,
                        study_key=study.description,
                    )
                )

    print(f"found {len(found)}:\n" + "\n".join(list(map(str, found))))
