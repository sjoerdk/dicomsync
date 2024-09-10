from dicomsync.routing import SwitchBoard
from tests.factories import DICOMRootFolderFactory


def test_switchboard(a_dicom_study_folder, mock_copy_functions):
    board = SwitchBoard()

    board.send(study=a_dicom_study_folder, place=DICOMRootFolderFactory())
    assert mock_copy_functions.copyfile.call_count == 3  # study folder had 3 files
