import click

from dicomsync.cli.base import DicomSyncContext, dicom_sync_command, get_key_for_place
from dicomsync.cli.click_parameter_types import (
    ImagingStudyParameterType,
    PlaceKeyParameterType,
)
from dicomsync.logs import get_module_logger
from dicomsync.routing import SwitchBoard

logger = get_module_logger("cli.send")


@dicom_sync_command(name="send")
@click.argument("study", type=ImagingStudyParameterType())
@click.argument("place", type=PlaceKeyParameterType())
@click.option(
    "--dry-run/--no-dry-run", help="Only simulate sending data", default=False
)
def cli_send(context: DicomSyncContext, study, place, dry_run):
    """Send a single imaging study (format 'place/study') to a place."""
    source_place, source_study_key = study
    source_study = source_place.get_study(source_study_key)

    settings = context.load_settings()
    board = SwitchBoard()
    logger.info(
        f"copying '{get_key_for_place(source_place, settings)}/{source_study}' "
        f"to '{get_key_for_place(place, settings)}'"
    )
    board.send(study=source_study, place=place, dry_run=dry_run)
