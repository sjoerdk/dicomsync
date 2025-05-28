"""Shared pytest fixtures and methods"""
import logging
import shutil
from pathlib import Path
from unittest.mock import Mock

import pytest
from _pytest.fixtures import fixture
from click.testing import CliRunner

from dicomsync.cli import base
from dicomsync.cli.base import DicomSyncContext, LazyDicomSyncContext
from dicomsync.core import Domain, Subject
from dicomsync.filesystem import (
    DICOMRootFolder,
    DICOMStudyFolder,
    ZippedDICOMRootFolder,
)
from dicomsync.persistence import DicomSyncSettings, DicomSyncSettingsFromFile
from dicomsync.xnat import XNATProjectPreArchive


@pytest.fixture(autouse=True)
def disable_log_printing():
    """Log messages were printed through test results. Stop that.

    Removing all handlers from root logger. Logs can still be caught and inspected
    by the `caplog` fixture, but nothing will be printed to console
    """

    logging.getLogger().handlers.clear()


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
def a_dicom_study_folder(tmpdir_factory) -> DICOMStudyFolder:
    study_folder = DICOMStudyFolder(
        subject=Subject(name="subject1"),
        description="study_1",
        place=DICOMRootFolder(path=Path(tmpdir_factory.mktemp("a_root_folder"))),
    )
    add_dummy_files(study_folder)
    return study_folder


@pytest.fixture
def some_settings(a_dicom_root_folder, a_dicom_zipped_folder) -> DicomSyncSettings:
    """A settings file containing one instance of each type of Place"""
    settings = DicomSyncSettings(
        places={"placeA": a_dicom_root_folder, "placeB": a_dicom_zipped_folder}
    )
    settings.places["placeC"] = XNATProjectPreArchive(
        server="https://server.com", user="user", project_name="project"
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


@fixture
def a_domain(tmpdir):
    """A domain containing three different Places with tmp directories"""
    return Domain(
        places={
            "a_folder": DICOMRootFolder(path=Path(tmpdir) / "a_root_folder"),
            "a_zip_folder": ZippedDICOMRootFolder(
                path=Path(tmpdir) / "a_zip_root_folder"
            ),
            "a_pre_archive": Mock(spec=XNATProjectPreArchive),
        }
    )


@fixture
def mock_settings(monkeypatch):
    """Settings loaded by CLI will be empty default settings.

    You can change settings by settings mock_settings.settings

    Returns
    -------
    MockSettings

    """
    raise NotImplementedError("Don't use mock_settings please.")

    class MockSettings:
        def __init__(self, settings):
            self.settings = settings
            monkeypatch.setattr(base, "load_settings", self.patch_settings())

        def patch_settings(self):
            def load_settings(folder):
                return self.settings

            return load_settings

    return MockSettings(DicomSyncSettings(places={}))


@fixture
def mock_copy_functions(monkeypatch):
    """Replace shutil and mkdir by mocks so no actual files get moved"""
    mocked = Mock(spec=shutil)

    monkeypatch.setattr("dicomsync.filesystem.shutil", mocked)
    monkeypatch.setattr("dicomsync.filesystem.Path.mkdir", Mock())

    return mocked


@fixture
def an_empty_settings_file(tmpdir):
    """An empty settings file on disk"""
    settings_path = DicomSyncSettingsFromFile.get_default_file(tmpdir)
    DicomSyncSettingsFromFile.init_from_settings(
        settings=DicomSyncSettings(places={}), path=Path(settings_path)
    ).save()
    return Path(settings_path)


@fixture
def a_file_based_context(an_empty_settings_file):
    """A dicom sync context linked to an empty file on disk"""
    return LazyDicomSyncContext(settings_path=an_empty_settings_file)


@fixture
def a_runner(a_file_based_context):
    """A click runner with in-memory settings and empty domain"""
    return MockContextCliRunner(mock_context=DicomSyncContext(domain=Domain({})))


@fixture
def a_runner_with_file(a_file_based_context):
    """A click runner that makes sure tmpdir is current dir and has empty settings
    file there.
    """
    return MockContextCliRunner(mock_context=a_file_based_context)
