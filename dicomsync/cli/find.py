from typing import Union

import click
from tabulate import tabulate

from dicomsync.cli.base import DicomSyncContext, dicom_sync_command
from dicomsync.cli.click_parameter_types import QueryParameterType
from dicomsync.references import StudyQuery
from dicomsync.logs import get_module_logger

logger = get_module_logger("cli.find")


@dicom_sync_command(name="find")
@click.argument("query", type=QueryParameterType())
def find(context: DicomSyncContext, query: Union[StudyQuery, str]):
    """Find DICOM studies in places"""

    # get current places
    domain = context.get_domain()
    if isinstance(query, StudyQuery):
        # user is asking for studies
        studies = list(domain.query_studies(query=query))
        suris = [domain.get_study_uri(x) for x in studies]
        click.echo(f"found {len(studies)}:\n" + "\n".join(map(str, suris)))

    elif isinstance(query, str):
        table = []
        for key, place in domain.query_places(place_query=query).items():
            table.append({"key": key, "place": str(place)})
        click.echo(tabulate(table, headers="keys"))
