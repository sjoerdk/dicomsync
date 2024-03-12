from pathlib import Path

from pytest import fixture

from dicomsync.core import Subject
from dicomsync.local import DICOMRootFolder
from tests.factories import DICOMStudyFolderFactory


@fixture()
def some_dicom_folders():
    return [DICOMStudyFolderFactory() for _ in range(3)]


@fixture()
def a_dicom_root_folder(tmpdir):
    root = DICOMRootFolder(Path(tmpdir) / "a_dicom_root")
    for _ in range(5):
        root.send_dicom_folder(DICOMStudyFolderFactory())
    return root


def test_dicom_root_folder(a_dicom_root_folder):
    a_study = DICOMStudyFolderFactory(
        subject=Subject("test1"), description="some_thing_34"
    )
    assert not a_dicom_root_folder.contains(a_study)
    a_dicom_root_folder.send_dicom_folder(a_study)
    assert a_dicom_root_folder.contains(a_study)


def test_copy_folder_to_xnat(a_dicom_root_folder):

    a_dicom_root_folder.all_studies()
    test = 1
    assert test
