"""Shared pytest fixtures and methods"""
from pathlib import Path

import pytest
from _pytest.fixtures import fixture
from click.testing import CliRunner

from dicomsync.cli.base import DicomSyncContext
from dicomsync.core import Subject
from dicomsync.local import DICOMRootFolder, DICOMStudyFolder, ZippedDICOMRootFolder
from dicomsync.persistence import DicomSyncSettings
from dicomsync.xnat import SerializableXNATProjectPreArchive


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


@pytest.fixture
def some_settings(a_dicom_root_folder, a_dicom_zipped_folder) -> DicomSyncSettings:
    """A settings file containing one instance of each type of Place"""
    settings = DicomSyncSettings(
        places={"placeA": a_dicom_root_folder, "placeB": a_dicom_zipped_folder}
    )
    settings.places["placeC"] = SerializableXNATProjectPreArchive(
        server="https://server.com", user="user", project="project"
    )
    return settings


class MockContextCliRunner(CliRunner):
    """a click.testing.CliRunner that always passes a mocked context to any call"""

    def __init__(self, *args, mock_context: DicomSyncContext, **kwargs):

        super().__init__(*args, **kwargs)
        self.mock_context = mock_context

    def invoke(
        self,
        cli,
        args=None,
        input=None,
        env=None,
        catch_exceptions=True,
        color=False,
        **extra,
    ):
        return super().invoke(
            cli,
            args,
            input,
            env,
            catch_exceptions,
            color,
            obj=self.mock_context,
        )


@fixture
def a_dicom_root_folder(tmpdir):
    folder = Path(tmpdir) / "dicomrootfolder"
    a_study = folder / "patient1" / "study1"
    a_study.mkdir(parents=True)
    create_dummy_files(a_study, files=3)
    return DICOMRootFolder(path=folder)


@fixture
def a_dicom_zipped_folder(tmpdir):
    folder = Path(tmpdir) / "dicomzipfolder"
    a_patient = folder / "patient1"
    a_patient.mkdir(parents=True)
    with open(a_patient / "study1.zip", "w") as f:
        f.write("")
    return ZippedDICOMRootFolder(path=folder)
