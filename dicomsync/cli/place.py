import click
from click import BadParameter
from tabulate import tabulate

from dicomsync.cli.base import DicomSyncContext
from dicomsync.local import DICOMRootFolder, ZippedDICOMRootFolder
from dicomsync.logs import get_module_logger

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
    for key, place in context.load_settings().places.items():
        table.append({"key": key, "place": str(place)})
    click.echo(tabulate(table, headers="keys"))


@click.command(short_help="Remove a place", name="remove")
@click.argument("key", type=str)
@click.pass_obj
def cli_remove(context: DicomSyncContext, key):
    """Remove a place by key"""
    settings = context.load_settings()
    try:
        del settings.places[key]
        settings.save()
    except KeyError as e:
        raise BadParameter(f"place '{key}' does not exist") from e
    click.echo(f'removed place "{key}"')


@click.group()
@click.pass_obj
def add(context: DicomSyncContext):
    """Manage places containing DICOM studies"""


@click.command(short_help="add DICOMRootFolder", name="dicom_root")
@click.pass_obj
@click.argument("key", type=str)
@click.argument("path_in", type=click.Path())
def add_dicom_root_folder(context: DicomSyncContext, path_in, key):
    """Show all places"""
    settings = context.load_settings()
    dicom_root_folder = DICOMRootFolder(path=path_in)
    logger.debug(f"Adding {dicom_root_folder}")
    places = settings.places
    if key in places:
        raise BadParameter(f"{key} already exists")
    else:
        settings.places[key] = dicom_root_folder
        settings.save()

    click.echo(f"added {dicom_root_folder} as '{key}'")


@click.command(short_help="add ZippedDICOMRootFolder", name="zipped_root")
@click.pass_obj
@click.argument("key", type=str)
@click.argument("path_in", type=click.Path())
def add_zipped_dicom_root_folder(context: DicomSyncContext, path_in, key):
    """Show all places"""
    settings = context.load_settings()
    folder = ZippedDICOMRootFolder(path=path_in)
    logger.debug(f"Adding {folder}")
    places = settings.places
    if key in places:
        raise BadParameter(f"{key} already exists")
    else:
        settings.places[key] = folder
        settings.save()

    click.echo(f"added {folder} as '{key}'")


place.add_command(cli_list)
place.add_command(cli_remove)

place.add_command(add)
add.add_command(add_dicom_root_folder)
add.add_command(add_zipped_dicom_root_folder)
