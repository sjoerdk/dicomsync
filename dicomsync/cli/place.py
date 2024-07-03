import click

from dicomsync.cli.base import DicomSyncContext


@click.group()
@click.pass_obj
def place(context: DicomSyncContext):
    """Manage places containing DICOM studies"""


@click.command(short_help="Show all places", name="list")
@click.pass_obj
def cli_list(context: DicomSyncContext):
    """Show all places"""
    print("Channels:")
    print(f"{context.settings.places}")


place.add_command(cli_list)
