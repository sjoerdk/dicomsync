"""Entrypoint for dicomsync CLI command. All subcommands are connected here."""
import click

from dicomsync.cli.base import configure_logging, get_context
from dicomsync.cli.place import place
from dicomsync.exceptions import DICOMSyncError, NoSettingsFoundError
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
    try:
        ctx.obj = get_context()
    except NoSettingsFoundError as e:
        logger.debug(str(e))
    except DICOMSyncError as e:
        logger.exception(e)
    except Exception as e:
        logger.exception(e)


main.add_command(place)
