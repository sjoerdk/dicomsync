from dicomsync.cli.base import DicomSyncContext
from dicomsync.cli.entrypoint import main
from dicomsync.persistence import DicomSyncSettings
from tests.conftest import MockContextCliRunner


def test_save_load_to_local_dir(tmpdir):
    # current dir does not contain any settings file
    runner = MockContextCliRunner(
        mock_context=DicomSyncContext(
            settings=DicomSyncSettings(places={}), current_dir=tmpdir
        )
    )

    response = runner.invoke(main, args=["-v", "place"])

    # No settings file should show warning message but not exit
    assert "No settings" in response.stdout
    assert response.exit_code == 0
