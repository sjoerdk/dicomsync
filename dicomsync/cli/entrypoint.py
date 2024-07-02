"""Entrypoint for dicomsync CLI command. All subcommands are connected here."""
import click

from dicomsync.cli.base import configure_logging, get_context


@click.group()
@click.option("-v", "--verbose", count=True)
@click.pass_context
def main(ctx, verbose):
    r"""Dicomsync - Check and sync medical image studies

    Use the commands below with -h for more info
    """
    configure_logging(verbose)
    ctx.obj = get_context()
