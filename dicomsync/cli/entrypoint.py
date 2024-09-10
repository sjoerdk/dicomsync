"""Entrypoint for dicomsync CLI command. All subcommands are connected here."""
import click

from dicomsync.cli.base import DicomSyncContext, configure_logging, get_context
from dicomsync.cli.place import place
from dicomsync.cli.send import cli_send
from dicomsync.logs import get_module_logger

logger = get_module_logger("entrypoint")


@click.group()
@click.option("-v", "--verbose", count=True)
@click.pass_context
def main(ctx, verbose):
    r"""Dicomsync - Check and sync medical image studies

    Use the commands below with -h for more info
    """
    configure_logging(verbose)
    ctx.obj = get_context()


@click.command(short_help="Show settings in current dir")
@click.pass_obj
def status(context: DicomSyncContext):
    """Show all places"""
    settings = context.load_settings()
    if hasattr(settings, "path"):
        click.echo(f"Reading settings from '{settings.path}'")
    else:
        click.echo("Reading settings from memory")

    place_keys = list(settings.places.keys())
    click.echo(f"{len(place_keys)} places defined in settings: {place_keys}")


main.add_command(status)
main.add_command(place)
main.add_command(cli_send)
