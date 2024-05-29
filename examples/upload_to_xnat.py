"""Take local study folders, zip and upload to xnat"""
import logging
from pathlib import Path

from dicomsync.core import Subject
from dicomsync.local import DICOMRootFolder, DICOMStudyFolder


logging.basicConfig(level=logging.DEBUG)

# Describe local files
subject1 = Subject(name="subject1")

local_study = DICOMStudyFolder(
    subject=subject1,
    description="a_study",
    path="/home/sjoerd/ticketdata/G00196/testdata/dicomroot/patient1/study1",
)


temp_location = DICOMRootFolder(Path("/tmp/dicomroot"))
temp_location.send_dicom_folder(local_study)

# create zip from this


# then upload zip to archive
# xnat_archive = XNATPreArchive()
