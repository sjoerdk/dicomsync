"""Test uploading local files to an xnat server"""
from pathlib import Path

from _pytest.fixtures import fixture

from dicomsync.core import Subject
from dicomsync.local import DICOMRootFolder, DICOMStudyFolder
from tests.factories import DICOMStudyFolderFactory
from tests.conftest import add_dummy_files


@fixture()
def a_dicom_root_folder(tmpdir):
    root = DICOMRootFolder(Path(tmpdir) / "a_dicom_root")
    for i in range(5):
        study_folder = DICOMStudyFolderFactory(
            path=Path(tmpdir) / "studyfolders" / f"study{i}"
        )
        add_dummy_files(study_folder)
        root.send_dicom_folder(study_folder)

    return root


def test_basic_upload(tmpdir):
    """I have a folder with dicom files. I'd like to upload to xnat"""

    a_dicom_folder = (
        Path(tmpdir) / "test_basic_upload" / "a_folder_with_filesa_dicom_folder"
    )
    study_folder = DICOMStudyFolder(
        subject=Subject(name="subject1"), description="study_1", path=a_dicom_folder
    )
    assert study_folder
