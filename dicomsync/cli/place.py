import click
from click import BadParameter
from tabulate import tabulate

from dicomsync.cli.base import DicomSyncContext, dicom_sync_command
from dicomsync.cli.click_parameter_types import PlaceKeyParameterType
from dicomsync.local import DICOMRootFolder, ZippedDICOMRootFolder
from dicomsync.logs import get_module_logger
from dicomsync.persistence import DicomSyncSettingsFromFile
from dicomsync.xnat import SerializableXNATProjectPreArchive

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


@click.command(short_help="Write empty settings file", name="init")
@click.pass_obj
def cli_init(context: DicomSyncContext):
    """Write empty settings file in current dir"""
    settings_path = DicomSyncSettingsFromFile.get_default_file(context.current_dir)
    logger.debug(f'Writing empty settings to "{settings_path}"')
    click.echo("Writing empty settings file to current dir")
    DicomSyncSettingsFromFile(path=settings_path, places={}).save()


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
    settings = context.load_settings()
    dicom_root_folder = DICOMRootFolder(path=path_in)
    logger.debug(f"Adding {dicom_root_folder}")
    places = settings.places
    if key in places:
        raise BadParameter(f"{key} already exists")
    else:
        settings.places[key] = dicom_root_folder
        settings.save()

    logger.info(f"added {dicom_root_folder} as '{key}'")


@click.command(short_help="add ZippedDICOMRootFolder", name="zipped_root")
@click.pass_obj
@click.argument("key", type=str)
@click.argument("path_in", type=click.Path())
def add_zipped_dicom_root_folder(context: DicomSyncContext, path_in, key):
    """Add folder containing patient/zip studies"""
    settings = context.load_settings()
    folder = ZippedDICOMRootFolder(path=path_in)
    logger.debug(f"Adding {folder}")
    places = settings.places
    if key in places:
        raise BadParameter(f"{key} already exists")
    else:
        settings.places[key] = folder
        settings.save()

    logger.info(f"added {folder} as '{key}'")


@click.command(short_help="add ZippedDICOMRootFolder", name="xnat_pre_archive")
@click.pass_obj
@click.argument("key", type=str)
@click.argument("server", type=str)
@click.argument("project", type=str)
@click.argument("user", type=str)
def add_xnat_pre_archive(context: DicomSyncContext, key, server, project, user):
    """Add XNAT pre-archive"""
    settings = context.load_settings()
    pre_archive = SerializableXNATProjectPreArchive(
        server=server, project=project, user=user
    )
    logger.debug(f"Adding {pre_archive}")
    places = settings.places
    if key in places:
        raise BadParameter(f"{key} already exists")
    else:
        settings.places[key] = pre_archive
        settings.save()

    logger.info(f"added {pre_archive} as '{key}'")


@dicom_sync_command()
@click.argument("place", type=PlaceKeyParameterType())
def ls(context: DicomSyncContext, place):
    """List studies in a place"""
    all = place.all_studies()
    patients = {str(x.subject) for x in all}
    click.echo(f"Found {len(all)} studies over {len(patients)} patients in {place}")
    click.echo("-----------------------------------")
    click.echo("\n".join([x.key() for x in place.all_studies()]))


place.add_command(cli_list)
place.add_command(cli_remove)
place.add_command(ls)
place.add_command(cli_init)

place.add_command(add)
add.add_command(add_dicom_root_folder)
add.add_command(add_zipped_dicom_root_folder)
add.add_command(add_xnat_pre_archive)
