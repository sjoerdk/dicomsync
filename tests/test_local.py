import logging
from pathlib import Path

from pytest import fixture

from dicomsync.core import Subject
from dicomsync.filesystem import (
    DICOMRootFolder,
    ZippedDICOMRootFolder,
)
from dicomsync.references import StudyQuery
from tests.conftest import add_dummy_files
from tests.factories import DICOMStudyFolderFactory


@fixture()
def some_dicom_folders():
    return [DICOMStudyFolderFactory() for _ in range(3)]


@fixture()
def an_empty_dicom_root_folder(tmpdir):
    """A dicom root folder with dummy data on disk"""
    return DICOMRootFolder(path=Path(tmpdir) / "a_dicom_root")


@fixture
def an_empty_zipfile_root_dir(tmpdir):
    return ZippedDICOMRootFolder(path=Path(tmpdir) / "a_zipfile_root")


def test_dicom_root_folder(an_empty_dicom_root_folder, tmpdir):
    """Send some studies to a root folder"""
    a_study = DICOMStudyFolderFactory(
        subject=Subject("test1"),
        description="some_thing_34",
    )
    add_dummy_files(a_study)
    assert not an_empty_dicom_root_folder.contains(a_study)
    an_empty_dicom_root_folder.send_dicom_folder(a_study)
    assert an_empty_dicom_root_folder.contains(a_study)


def test_dicom_root_folder_paths(an_empty_dicom_root_folder):
    """Exposes a bug with duplicated patient names in path"""
    # create a single dicom patient/study structure inside root

    root = an_empty_dicom_root_folder
    expected_path = root.path / "patient1" / "study1"
    expected_path.mkdir(parents=True, exist_ok=False)
    studies = list(
        root._query_studies(query=StudyQuery.init_from_string("anything:patient1*"))
    )

    study = studies[0]
    assert study.path == expected_path


def test_dicom_root_folder_paths_exact_match(an_empty_dicom_root_folder):
    """A study query that matches exactly a single study should result in that study."""
    # create a single dicom patient/study structure inside root

    root = an_empty_dicom_root_folder
    expected_path = root.path / "patient1" / "study1"
    expected_path.mkdir(parents=True, exist_ok=False)

    studies = list(
        root._query_studies(
            query=StudyQuery.init_from_string("anything:patient1/study1")
        )
    )
    assert len(studies) == 1


def test_zip(tmpdir_factory, an_empty_zipfile_root_dir, caplog):
    """Send a folder of files to a zipped root folder"""

    study_folder = DICOMStudyFolderFactory(
        subject=Subject(name="subject1"),
        description="study_1",
    )
    add_dummy_files(study_folder)

    caplog.set_level(logging.DEBUG)
    zip_root: ZippedDICOMRootFolder = an_empty_zipfile_root_dir
    zip_root.send_dicom_folder(study_folder)

    # zip root should now know it has received the study
    assert zip_root.contains(study_folder)
    zipped_study = [x for x in zip_root.all_studies()][0]
    assert zipped_study.description == "study_1"
