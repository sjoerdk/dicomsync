import click

from dicomsync.cli.base import DicomSyncContext, dicom_sync_command, get_key_for_place
from dicomsync.cli.click_parameter_types import (
    ImagingStudyParameterType,
    PlaceKeyParameterType,
)


@dicom_sync_command(name="send")
@click.argument("study", type=ImagingStudyParameterType())
@click.argument("place", type=PlaceKeyParameterType())
def cli_send(context: DicomSyncContext, study, place):
    """Send a single imaging study (format 'place/study') to a place."""
    source_place, source_study = study
    settings = context.load_settings()
    click.echo(
        f"copying '{get_key_for_place(source_place, settings)}/{source_study}' "
        f"to '{get_key_for_place(place, settings)}'"
    )
