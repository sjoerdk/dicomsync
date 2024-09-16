from pathlib import Path
from unittest.mock import Mock

from pytest import fixture

from dicomsync.cli.base import DicomSyncContext
from dicomsync.cli.entrypoint import main
from dicomsync.local import DICOMRootFolder, ZippedDICOMRootFolder
from dicomsync.xnat import SerializableXNATProjectPreArchive
from tests.conftest import MockContextCliRunner


@fixture
def a_runner(tmpdir):
    """A click runner that makes sure tmpdir is current dir"""
    return MockContextCliRunner(mock_context=DicomSyncContext(current_dir=tmpdir))


@fixture
def a_runner_with_settings(a_runner, tmpdir, mock_settings):
    """A runner with some configured places"""
    a_root_folder = Path(tmpdir) / "a_root_folder"
    a_zip_root_folder = Path(tmpdir) / "a_zip_root_folder"
    a_pre_archive = Mock(spec=SerializableXNATProjectPreArchive)
    mock_settings.settings.places = {
        "a_folder": DICOMRootFolder(path=a_root_folder),
        "a_zip_folder": ZippedDICOMRootFolder(path=a_zip_root_folder),
        "a_pre_archive": a_pre_archive,
    }
    return a_runner


def test_save_load_to_local_dir(a_runner_with_settings):
    """Simply run the command most basic"""

    runner = a_runner_with_settings
    response = runner.invoke(
        main,
        args=["-v", "send", "a_folder:patient/study", "a_pre_archive"],
        catch_exceptions=True,
    )
    # a_folder/study does not exist, so exception
    assert "not found" in str(response.exception)
    assert response.exit_code == 1
