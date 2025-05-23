"""Entrypoint for dicomsync CLI command. All subcommands are connected here."""
import click

from dicomsync.cli.base import DicomSyncContext, configure_logging, init_context
from dicomsync.cli.find import find
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
    if not ctx.obj:
        ctx.obj = init_context()


@click.command(short_help="Show settings in current dir")
@click.pass_obj
def status(context: DicomSyncContext):
    """Show all places"""

    place_keys = list(context.get_domain().places.keys())
    click.echo(f"{len(place_keys)} places defined in settings: {place_keys}")


main.add_command(status)
main.add_command(place)
main.add_command(cli_send)
main.add_command(find)
