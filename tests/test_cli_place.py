from pytest import fixture

from dicomsync.cli.base import DicomSyncContext
from dicomsync.cli.entrypoint import main
from tests.conftest import MockContextCliRunner


@fixture
def a_runner(tmpdir):
    """A click runner that makes sure tmpdir is current dir"""
    return MockContextCliRunner(mock_context=DicomSyncContext(current_dir=tmpdir))


def test_save_load_to_local_dir(a_runner):
    # current dir does not contain any settings file

    response = a_runner.invoke(
        main, args=["-v", "place", "list"], catch_exceptions=False
    )

    # No settings file should show warning message
    assert "No settings" in response.stdout
    assert response.exit_code == 2


def test_place_add_dicom_root(mock_settings, a_runner):
    """Run CLI to add some things and check"""
    places = mock_settings.settings.places
    assert not places
    response = a_runner.invoke(
        main,
        args=["-v", "place", "add", "dicom_root", "key_1", "/a_folder"],
        catch_exceptions=False,
    )
    assert response.exit_code == 0
    assert "key_1" in places


def test_place_add_zip_root(mock_settings, a_runner):
    """Run CLI to add some things and check"""
    places = mock_settings.settings.places
    assert not places
    response = a_runner.invoke(
        main,
        args=["-v", "place", "add", "zipped_root", "key_2", "/a_folder2"],
        catch_exceptions=False,
    )
    assert response.exit_code == 0
    assert "key_2" in places


def test_place_add_xnat_pre_archive(mock_settings, a_runner):
    """Run CLI to add some things and check"""
    places = mock_settings.settings.places
    assert not places
    response = a_runner.invoke(
        main,
        args=[
            "-v",
            "place",
            "add",
            "xnat_pre_archive",
            "key_3",
            "server",
            "project1",
            "a_user",
        ],
        catch_exceptions=False,
    )
    assert response.exit_code == 0
    assert "key_3" in places
    assert places["key_3"].server == "server"
    assert places["key_3"].project == "project1"
    assert places["key_3"].user == "a_user"
