from pathlib import Path
from typing import Dict

from dicomsync.cli.find import find
from dicomsync.core import Subject
from dicomsync.local import DICOMRootFolder, DICOMStudyFolder
from dicomsync.persistence import SerializablePlace
from tests.factories import DICOMStudyFolderFactory


def add_path_on_disk(study_folder: DICOMStudyFolder, tmp_root):
    """Change study_folder path to a unique valid path that exists on disk"""
    study_folder.path = (
        Path(tmp_root) / str(study_folder.subject) / study_folder.description
    )
    study_folder.path.mkdir(parents=True, exist_ok=True)
    return study_folder


def convert_to_places(input_dict, tmp_root) -> Dict[str, SerializablePlace]:
    """Quick way to define a DICOMRootFolder with some mock subjects/patients

    Parameters
    ----------
    Dict[str, Dict[str, List[str]]]

    Example
    -------
    Example input
        {"place1": {"Patient1": ["Study1_A", "Study2_B"],
                    "Patient2": ["Study3_A", "Study4_B"]}}

    """
    places = {}
    for place, patients in input_dict.items():

        place_path = Path(tmp_root / "a_dicom_root" / place)
        place_path.mkdir(parents=True, exist_ok=True)
        places[place] = DICOMRootFolder(path=place_path)

        for patient, studies in patients.items():
            for study_name in studies:
                study = DICOMStudyFolderFactory(
                    subject=Subject(patient), description=study_name
                )
                study = add_path_on_disk(study, Path(tmp_root))
                places[place].send_dicom_folder(study)
    return dict(places)


def test_find(mock_settings, a_runner, tmp_path):

    # add some mock place for
    mock_place = {
        "place1": {
            "Patient1": ["Study1_A", "Study2_B"],
            "Patient2": ["Study3_A", "Study4_B"],
        },
    }

    mock_settings.settings.places = convert_to_places(
        mock_place, tmp_root=Path(tmp_path)
    )

    response = a_runner.invoke(
        find, args=["place1:patient1/key_1"], catch_exceptions=False
    )

    assert response.exit_code == 0
