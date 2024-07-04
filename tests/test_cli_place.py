from dicomsync.cli.base import DicomSyncContext
from dicomsync.cli.entrypoint import main
from tests.conftest import MockContextCliRunner


def test_save_load_to_local_dir(tmpdir):
    # current dir does not contain any settings file
    runner = MockContextCliRunner(mock_context=DicomSyncContext(current_dir=tmpdir))

    response = runner.invoke(main, args=["-v", "place", "list"], catch_exceptions=False)

    # No settings file should show warning message
    assert "No settings" in response.stdout
    assert response.exit_code == 2
