from pathlib import Path
from unittest.mock import Mock

from pytest import fixture

from dicomsync.cli.entrypoint import main
from dicomsync.cli.send import cli_send
from dicomsync.filesystem import DICOMRootFolder, ZippedDICOMRootFolder
from dicomsync.xnat import XNATProjectPreArchive


@fixture
def some_settings(a_runner, tmpdir, mock_settings):
    """Settings with some configured tmp places"""
    mock_settings.settings.places = {
        "a_folder": DICOMRootFolder(path=Path(tmpdir) / "a_root_folder"),
        "a_zip_folder": ZippedDICOMRootFolder(path=Path(tmpdir) / "a_zip_root_folder"),
        "a_pre_archive": Mock(spec=XNATProjectPreArchive),
    }
    return mock_settings


def test_save_load_to_local_dir(a_runner):
    """Simply run the command most basic"""

    runner = a_runner
    response = runner.invoke(
        main,
        args=["-v", "send", "a_folder:patient/study", "a_pre_archive"],
        catch_exceptions=False,
    )
    # a_folder/study does not exist, so exception
    assert '"a_pre_archive" not found' in str(response.output)
    assert response.exit_code == 2


def test_send_existing(a_runner, a_domain, a_dicom_root_folder):
    """Send some studies, part of which already exist in target. Should filter."""
    a_runner.mock_context._domain = a_domain

    # a_folder contains one study patient1/study1
    a_domain.places["a_folder"] = a_dicom_root_folder

    # nothing has been sent yet to destination
    assert not [x for x in a_domain.places["a_zip_folder"].all_studies()]

    # first send should send the one study
    response = a_runner.invoke(
        cli_send,
        args=["a_folder:patient1/study1", "a_zip_folder"],
        catch_exceptions=False,
    )
    assert response.exit_code == 0

    # which then appears in the destination
    assert len([x for x in a_domain.places["a_zip_folder"].all_studies()]) == 1

    # Sending again will send nothing extra, though. It should be detected as already
    # there.
    response = a_runner.invoke(
        cli_send,
        args=["a_folder:patient1/study1", "a_zip_folder"],
        catch_exceptions=False,
    )

    assert not response.exception
    assert len([x for x in a_domain.places["a_zip_folder"].all_studies()]) == 1
