"""Test basic functionality of CLI"""
import os
from pathlib import Path
from unittest.mock import Mock

from click.testing import CliRunner

from dicomsync.cli.base import DicomSyncContext
from dicomsync.cli.entrypoint import main
from dicomsync.core import Domain
from dicomsync.persistence import (
    DEFAULT_SETTINGS_FILE_NAME,
    DicomSyncSettingsFromFile,
)
from tests.conftest import MockContextCliRunner


def test_save_load_to_local_dir(tmpdir):
    """Test running if there are no settings"""
    # current dir does not contain any settings file
    runner = MockContextCliRunner(
        mock_context=DicomSyncContext(domain=Mock(spec=Domain))
    )

    response = runner.invoke(main, args=["-v", "place"], catch_exceptions=False)
    # no error should have been raised as no settings are needed here
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
