"""Take local study folders, zip and upload to xnat"""

import logging

from dicomsync.core import Domain
from dicomsync.filesystem import DICOMRootFolder, ZippedDICOMRootFolder
from pathlib import Path

from dicomsync.routing import SwitchBoard
from dicomsync.xnat import XNATProjectPreArchive

# ================= logging ====================================================

logging.basicConfig(level=logging.DEBUG)
logging.getLogger("PIL").level = logging.WARNING
logging.getLogger("urllib3").level = logging.DEBUG
logger = logging.getLogger()

# ================= define the places we will be working with ==================

# the dicom studies dir in patient/study format
dicom_root_folder = DICOMRootFolder(path=Path("/tmp/dicomroot"))

# a location for zip files. Local
zip_folder = ZippedDICOMRootFolder(path=Path("/tmp/zipfiles"))

# Before running, set "XNAT_PASS" environment variable
# (using for example EXPORT XNAT_PASS='yourpassword')
xnat_archive = XNATProjectPreArchive(
    server="https://xnathost", user="user", project_name="myproject"
)

# ================= Define convenient helper objects ===========================

# To make copying and querying easier, name each place
domain = Domain(
    places={
        "dicom_folder": dicom_root_folder,
        "zip_folder": zip_folder,
        "xnat_archive": xnat_archive,
    }
)

# To be able to send any study to any place (or receive informative error)
switchboard = SwitchBoard()

# ================= Ensure things are like they should be ========================
# Query format is <place_name>:<patient>/<study>. You can use wildcards anywhere.

studies = [x for x in domain.query_studies("dicom_folder:*")]
logger.info(f"Found {len(studies)} studies")

# zip the studies
for study in studies:
    switchboard.send(study=study, place=zip_folder)

# send zipped to xnat
zipped = [x for x in domain.query_studies("zip_folder:*")]
logger.info(f"Found {len(zipped)} zipped studies")
logger.info(f"Sending to {xnat_archive}")
for zip_study in zipped:
    switchboard.send(study=zip_study, place=xnat_archive)
