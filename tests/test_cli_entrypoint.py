"""Test basic functionality of CLI"""
import os
from pathlib import Path

from click.testing import CliRunner

from dicomsync.cli.base import DicomSyncContext
from dicomsync.cli.entrypoint import main
from dicomsync.persistence import (
    DEFAULT_SETTINGS_FILE_NAME,
    DicomSyncSettings,
    DicomSyncSettingsFromFile,
)
from tests.conftest import MockContextCliRunner


def test_save_load_to_local_dir(tmpdir):
    """Test running if there are no settings"""
    # current dir does not contain any settings file
    runner = MockContextCliRunner(
        mock_context=DicomSyncContext(
            settings=DicomSyncSettings(places={}), current_dir=tmpdir
        )
    )

    response = runner.invoke(
        main, args=["-v", "place"]
    )  # -v to ensure debug message gets printed.
    # 'place' arg to trigger settings read

    # No settings file should show warning message but not exit
    assert "No settings" in response.stdout
    assert response.exit_code == 0


def test_load_save_settings(tmpdir, some_settings, monkeypatch):
    """Simple loading of settings from working dir"""

    # create some settings on disk
    settings_path = Path(tmpdir) / DEFAULT_SETTINGS_FILE_NAME
    settings = DicomSyncSettingsFromFile.init_from_settings(
        settings=some_settings, path=settings_path
    )
    settings.save()

    # make sure current working dir is set to test folder
    monkeypatch.setattr(os, "getcwd", lambda: Path(tmpdir))

    # now these should be loaded automatically
    runner = CliRunner()

    response = runner.invoke(main, args=["-v", "place", "list"], catch_exceptions=False)

    # this should have read settings from disk and listed three places
    assert response.exit_code == 0
    for x in ["placeA", "placeB", "placeC"]:
        assert x in response.stdout
