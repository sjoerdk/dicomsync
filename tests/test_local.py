import logging
from pathlib import Path

from pytest import fixture

from dicomsync.core import Subject
from dicomsync.local import DICOMRootFolder, DICOMStudyFolder, ZippedDICOMRootFolder
from tests.conftest import add_dummy_files
from tests.factories import DICOMStudyFolderFactory


@fixture()
def some_dicom_folders():
    return [DICOMStudyFolderFactory() for _ in range(3)]


@fixture()
def a_dicom_study_folder(tmpdir):
    study_folder = DICOMStudyFolder(
        subject=Subject(name="subject1"),
        description="study_1",
        path=Path(tmpdir) / "subject1" / "study_1",
    )
    add_dummy_files(study_folder)
    return study_folder


@fixture()
def an_empty_dicom_root_folder(tmpdir):
    """A dicom root folder with dummy data on disk"""
    return DICOMRootFolder(Path(tmpdir) / "a_dicom_root")


@fixture
def an_empty_zipfile_root_dir(tmpdir):
    return ZippedDICOMRootFolder(Path(tmpdir) / "a_zipfile_root")


def test_dicom_root_folder(an_empty_dicom_root_folder, tmpdir):
    """Send some studies to a root folder"""
    a_study = DICOMStudyFolderFactory(
        subject=Subject("test1"),
        description="some_thing_34",
        path=Path(tmpdir) / "dicom_root_folder",
    )
    add_dummy_files(a_study)
    assert not an_empty_dicom_root_folder.contains(a_study)
    an_empty_dicom_root_folder.send_dicom_folder(a_study)
    assert an_empty_dicom_root_folder.contains(a_study)


def test_zip(tmpdir, an_empty_zipfile_root_dir, caplog):
    """Send a folder of files to a zipped root folder"""
    study_folder = DICOMStudyFolder(
        subject=Subject(name="subject1"),
        description="study_1",
        path=Path(tmpdir) / "subject1" / "study_1",
    )
    add_dummy_files(study_folder)

    caplog.set_level(logging.DEBUG)
    zip_root: ZippedDICOMRootFolder = an_empty_zipfile_root_dir
    zip_root.send_dicom_folder(study_folder)

    # zip root should now know it has received the study
    assert zip_root.contains(study_folder)
    zipped_study = zip_root.all_studies()[0]
    assert zipped_study.description == "study_1"
