import click
from click import BadParameter
from tabulate import tabulate

from dicomsync.cli.base import DicomSyncContext, dicom_sync_command
from dicomsync.filesystem import DICOMRootFolder, ZippedDICOMRootFolder
from dicomsync.logs import get_module_logger
from dicomsync.xnat import XNATProjectPreArchive

logger = get_module_logger("cli.place")


@click.group()
@click.pass_obj
def place(context: DicomSyncContext):
    """Manage places containing DICOM studies"""


@click.command(short_help="Show all places", name="list")
@click.pass_obj
def cli_list(context: DicomSyncContext):
    """Show all places"""
    table = []
    domain = context.get_domain()
    for key, place in domain.query_places("*").items():
        table.append({"key": key, "place": str(place)})
    click.echo(tabulate(table, headers="keys"))


@click.command(short_help="Write empty settings file", name="init")
@click.pass_obj
def cli_init(context: DicomSyncContext):
    """Write empty settings file in current dir"""
    path = context.save_settings()
    logger.debug(f'Wrote empty settings to "{str(path)}"')


@click.command(short_help="Remove a place", name="remove")
@click.argument("key", type=str)
@click.pass_obj
def cli_remove(context: DicomSyncContext, key):
    """Remove a place by key"""
    domain = context.get_domain()
    try:
        del domain.places[key]
        context.save_settings()
    except KeyError as e:
        raise BadParameter(f"place '{key}' does not exist") from e
    logger.info(f'removed place "{key}"')


@click.group()
@click.pass_obj
def add(context: DicomSyncContext):
    """Manage places containing DICOM studies"""


@click.command(short_help="add DICOMRootFolder", name="dicom_root")
@click.pass_obj
@click.argument("key", type=str)
@click.argument("path_in", type=click.Path())
def add_dicom_root_folder(context: DicomSyncContext, path_in, key):
    """Add folder containing patient/study folders"""

    add_place(context=context, place=DICOMRootFolder(path=path_in), key=key)


@click.command(short_help="add ZippedDICOMRootFolder", name="zipped_root")
@click.pass_obj
@click.argument("key", type=str)
@click.argument("path_in", type=click.Path())
def add_zipped_dicom_root_folder(context: DicomSyncContext, path_in, key):
    """Add folder containing patient/zip studies"""

    add_place(context=context, place=ZippedDICOMRootFolder(path=path_in), key=key)


@click.command(short_help="add XNAT pre-archive", name="xnat_pre_archive")
@click.pass_obj
@click.argument("key", type=str)
@click.argument("server", type=str)
@click.argument("project", type=str)
@click.argument("user", type=str)
def add_xnat_pre_archive(context: DicomSyncContext, key, server, project, user):
    """Add XNAT pre-archive"""
    add_place(
        context=context,
        place=XNATProjectPreArchive(server=server, project_name=project, user=user),
        key=key,
    )


def add_place(context, place, key):
    """Add place to the domain in current context and save to settings"""
    domain = context.get_domain()
    logger.debug(f"Adding {place}")
    try:
        domain.add_place(place, key)
        context.save_settings()
    except KeyError as e:
        raise BadParameter(message=str(e)) from e

    logger.info(f"added {place} as '{key}'")


@dicom_sync_command()
@click.argument("place_name", type=click.STRING)
def ls(context: DicomSyncContext, place_name):
    """List studies in a place"""
    studies = [x for x in context.get_domain().query_studies(place_name + ":*")]
    patients = {str(x.subject) for x in studies}
    click.echo(f"Found {len(studies)} studies over {len(patients)} patients in {place}")
    click.echo("-----------------------------------")
    click.echo("\n".join([str(x.key()) for x in studies]))


place.add_command(cli_list)
place.add_command(cli_remove)
place.add_command(ls)
place.add_command(cli_init)

place.add_command(add)
add.add_command(add_dicom_root_folder)
add.add_command(add_zipped_dicom_root_folder)
add.add_command(add_xnat_pre_archive)
