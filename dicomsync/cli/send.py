import click

from dicomsync.cli.base import DicomSyncContext, dicom_sync_command
from dicomsync.cli.click_parameter_types import StudyQueryParameterType

from dicomsync.references import StudyQuery
from dicomsync.logs import get_module_logger
from dicomsync.routing import SwitchBoard

logger = get_module_logger("cli.send")


@dicom_sync_command(name="send")
@click.argument("study_query", type=StudyQueryParameterType())
@click.argument("place_key", type=click.STRING)
@click.option(
    "--dry-run/--no-dry-run", help="Only simulate sending data", default=False
)
def cli_send(
    context: DicomSyncContext,
    study_query: StudyQuery,
    place_key,
    dry_run,
):
    """Send one or more imaging studies to a place."""
    logger.info(f"Sending all studies matching {study_query} to '{place_key}'")

    domain = context.get_domain()
    place = domain.get_place(place_key)
    # collect all studies here to be able to print how many there are

    studies_to_send = [x for x in domain.query_studies(query=study_query)]

    logger.info(f"found {len(studies_to_send)} studies matching {study_query}.")

    logger.debug(f"Checking for existing studies in {place}")
    studies_dup, studies_org = place.find_duplicates(studies_to_send)

    if studies_org:
        to_send = "\n".join([str(x) for x in studies_org])
        logger.info(
            f"Found '{len(studies_dup)}' duplicate studies." f"Sending rest:{to_send}"
        )
        board = SwitchBoard()
        for study in studies_org:
            logger.info(f"processing {study}")
            board.send(study=study, place=place, dry_run=dry_run)
        logger.debug(f"Finished sending {len(studies_org)} studies for {study_query}")
    else:
        logger.info(f"Found {len(studies_dup)} duplicate studies.")
        logger.info("All studies were duplicates. Not sending anything.")
