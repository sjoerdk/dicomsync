"""Take local study folders, zip and upload to xnat"""

import logging
import os

from dicomsync.filesystem import DICOMRootFolder, ZippedDICOMRootFolder
from pathlib import Path

from dicomsync.ui import summarize_results
from dicomsync.xnat import XNATConnectionFactory, XNATProjectPreArchive

# ================= logging ====================================================

logging.basicConfig(level=logging.DEBUG)
logging.getLogger("PIL").level = logging.WARNING
logging.getLogger("urllib3").level = logging.DEBUG
logger = logging.getLogger()

# ================= define objects we will be working with =======================

# the dicom studies dir in patient/study format
dicom_root_folder = DICOMRootFolder(path=Path("/tmp/dicomroot"))

# a location for zip files. Local
zip_folder = ZippedDICOMRootFolder(path=Path("/tmp/zipfiles"))

session_factory = XNATConnectionFactory(
    server="https://xnathost", user="user", password=os.environ["XNAT_PASS"]
)

# ================= Ensure things are like they should be ========================

# Work with these studies:
studies = dicom_root_folder.all_studies()
logger.info(f"Found {len(studies)} studies")

# These should be zipped
logger.info("Checking zip dir")
results = [zip_folder.assert_has_zip(study) for study in studies]
logger.info(summarize_results(results))

# send to xnat
with session_factory.get_connection() as connection:
    project = XNATProjectPreArchive(connection=connection, project_name="myproject")
    logger.info(f"Sending to {project}")
    results = [project.assert_has_study(study) for study in zip_folder.all_studies()]
    logger.info(summarize_results(results))
