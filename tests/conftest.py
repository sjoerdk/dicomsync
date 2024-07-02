"""Shared pytest fixtures and methods"""
from pathlib import Path

import pytest

from dicomsync.core import Subject
from dicomsync.local import DICOMStudyFolder


def add_dummy_files(studyfolder: DICOMStudyFolder, files=3):
    """Make sure there are some files in studyfolder path"""
    return create_dummy_files(studyfolder.path, files)


def create_dummy_files(path_in, files=3):
    if not path_in.glob("*"):
        raise ValueError(f"Path {path_in} is not empty. Not writing dummy files")
    path_in.mkdir(exist_ok=True, parents=True)
    for i in range(files):
        with open(path_in / f"file{i}", "w") as f:
            f.write("content")


@pytest.fixture
def a_folder_with_files(tmpdir):
    """A single folder containing some dummy files (non-dicom)"""

    a_dicom_folder = (
        Path(tmpdir) / "test_basic_upload" / "a_folder_with_filesa_dicom_folder"
    )
    create_dummy_files(a_dicom_folder)
    return a_dicom_folder


@pytest.fixture()
def a_dicom_study_folder(tmpdir) -> DICOMStudyFolder:
    study_folder = DICOMStudyFolder(
        subject=Subject(name="subject1"),
        description="study_1",
        path=Path(tmpdir) / "subject1" / "study_1",
    )
    add_dummy_files(study_folder)
    return study_folder
