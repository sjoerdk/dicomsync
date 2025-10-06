"""Test basic functionality of CLI"""
import os
from pathlib import Path

from click.testing import CliRunner

from dicomsync.cli.entrypoint import main
from dicomsync.persistence import (
    DEFAULT_SETTINGS_FILE_NAME,
    DicomSyncSettingsFromFile,
)


def test_save_load_to_local_dir(tmp_path):
    """Test running if there are no settings"""
    # current dir does not contain any settings file
    runner = CliRunner()

    # trying to run a list command, which needs settings file, will generate an error
    response = runner.invoke(main, args=["-v", "place", "list"], catch_exceptions=False)
    assert "No settings file" in response.output

    # Running command without parameters does not need settings. Should not care
    # about settings file and thus generate no error
    response2 = runner.invoke(main, args=["-v", "place"], catch_exceptions=False)
    assert "No settings file" not in response2.output


def test_load_save_settings(tmp_path, some_settings, monkeypatch):
    """Simple loading of settings from working dir"""

    # create some settings on disk
    settings_path = tmp_path / DEFAULT_SETTINGS_FILE_NAME
    settings = DicomSyncSettingsFromFile.init_from_settings(
        settings=some_settings, path=settings_path
    )
    settings.save()

    # make sure current working dir is set to test folder
    monkeypatch.setattr(os, "getcwd", lambda: tmp_path)

    # now these should be loaded automatically
    runner = CliRunner()

    response = runner.invoke(main, args=["-v", "place", "list"], catch_exceptions=False)

    # this should have read settings from disk and listed three places
    assert response.exit_code == 0
    for x in ["placeA", "placeB", "placeC"]:
        assert x in response.stdout


def test_init(tmp_path, some_settings, monkeypatch):
    """Simple loading of settings from working dir"""
    runner = CliRunner()

    # make sure current working dir is set unique to this test
    monkeypatch.setattr(os, "getcwd", lambda: Path(tmp_path))

    # init should create this file when called
    expected_settings_file = Path(tmp_path) / DEFAULT_SETTINGS_FILE_NAME

    # the file does not exist at first
    assert not expected_settings_file.exists()

    # after calling init it should exist
    response = runner.invoke(main, args=["init"], catch_exceptions=False)
    assert response.exit_code == 0
    assert expected_settings_file.exists()

    # calling it again should yield an error
    response2 = runner.invoke(main, args=["init"], catch_exceptions=False)
    assert response2.exit_code == 2
