"""Entrypoint for dicomsync CLI command. All subcommands are connected here."""
from pathlib import Path

import click

from dicomsync.cli.base import DicomSyncContext, configure_logging, init_context
from dicomsync.cli.compare import compare
from dicomsync.cli.find import find
from dicomsync.cli.place import place
from dicomsync.cli.send import cli_send
from dicomsync.logs import get_module_logger
from dicomsync.persistence import (
    DEFAULT_SETTINGS_FILE_NAME,
    DicomSyncSettings,
    DicomSyncSettingsFromFile,
)

logger = get_module_logger("entrypoint")


@click.group()
@click.option("-v", "--verbose", count=True)
@click.pass_context
def main(ctx, verbose):
    r"""Dicomsync - Check and sync medical image studies

    Use the commands below with -h for more info
    """
    configure_logging(verbose)
    if not ctx.obj:
        ctx.obj = init_context()


@click.command(short_help="Show settings in current dir")
@click.pass_obj
def status(context: DicomSyncContext):
    """Show all places"""

    place_keys = list(context.get_domain().places.keys())
    click.echo(f"{len(place_keys)} places defined in settings: {place_keys}")


@click.command(short_help="Create empty settings file in current dir")
@click.pass_obj
def init(context: DicomSyncContext):
    """Create empty settings file in current dir"""
    settings_file = Path(context.get_cwd()) / DEFAULT_SETTINGS_FILE_NAME
    if settings_file.exists():
        raise click.UsageError(f"Settings file already exists at '{settings_file}'")
    DicomSyncSettingsFromFile.init_from_settings(
        settings=DicomSyncSettings(places={}), path=settings_file
    ).save()

    click.echo(f"Created empty settings file at '{settings_file}'")


main.add_command(init)
main.add_command(status)
main.add_command(place)
main.add_command(cli_send)
main.add_command(find)
main.add_command(compare)
