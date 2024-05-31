"""Take local study folders, zip and upload to xnat"""
import logging
import os
from pathlib import Path

from dicomsync.core import Subject
from dicomsync.local import DICOMRootFolder, DICOMStudyFolder
from dicomsync.xnat import XNATProjectPreArchive, XNATSessionFactory

logging.basicConfig(level=logging.DEBUG)

# Describe local files
subject1 = Subject(name="subject1")

local_study = DICOMStudyFolder(
    subject=subject1,
    description="a_study",
    path="/home/sjoerd/ticketdata/G00196/testdata/dicomroot/patient1/study1",
)


temp_location = DICOMRootFolder(Path("/tmp/dicomroot"))
# temp_location.send_dicom_folder(local_study)

# create zip from this


# then upload zip to archive
# xnat_archive = XNATProjectPreArchive()
session_factory = XNATSessionFactory(
    server="https://xnat.bmia.nl/", user="skerkstra", password=os.environ["XNAT_PASS"]
)

with session_factory.get_session() as connection:
    project = XNATProjectPreArchive(session=connection, project_name="mrcleandist")
    studies = project.all_studies()

for study in studies:
    print(f"{study} - {study.date_uploaded}")
