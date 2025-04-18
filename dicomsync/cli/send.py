from typing import Tuple

import click

from dicomsync.cli.base import DicomSyncContext, dicom_sync_command, get_key_for_place
from dicomsync.cli.click_parameter_types import (
    StudyURIParameterType,
    PlaceKeyParameterType,
)
from dicomsync.core import Place
from dicomsync.references import StudyURI
from dicomsync.exceptions import StudyNotFoundError
from dicomsync.logs import get_module_logger
from dicomsync.routing import SwitchBoard

logger = get_module_logger("cli.send")


@dicom_sync_command(name="send")
@click.argument("study_uri", type=StudyURIParameterType())
@click.argument("place", type=PlaceKeyParameterType())
@click.option(
    "--dry-run/--no-dry-run", help="Only simulate sending data", default=False
)
def cli_send(
    context: DicomSyncContext,
    study_uri: Tuple[Place, StudyURI],
    place,
    dry_run,
):
    """Send a single imaging study (format 'place/study') to a place."""
    source_place, source_study_identifier = study_uri
    try:
        source_study = source_place.get_study(source_study_identifier.study_key)
    except StudyNotFoundError:
        slug = source_study_identifier.to_slug()
        logger.debug(
            f'Study "{source_study_identifier}" not found. Trying slug "{slug}"'
        )
        source_study = source_place.get_study(slug.study_key)

    settings = context.load_settings()
    board = SwitchBoard()
    logger.info(
        f"copying '{get_key_for_place(source_place, settings)}/{source_study}' "
        f"to '{get_key_for_place(place, settings)}'"
    )
    board.send(study=source_study, place=place, dry_run=dry_run)
