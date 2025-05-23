import pytest

from dicomsync.cli.find import find
from dicomsync.core import Domain, Subject
from tests.factories import DICOMRootFolderFactory, DICOMStudyFolderFactory


def convert_to_places(input_dict):
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
    for place_name, patients in input_dict.items():
        place = DICOMRootFolderFactory()
        places[place_name] = place

        for patient, studies in patients.items():
            for study_name in studies:
                study = DICOMStudyFolderFactory(
                    subject=Subject(patient), description=study_name, place=place
                )
                study.path.mkdir(parents=True, exist_ok=False)

    return places


@pytest.mark.parametrize(
    "query,expected_output",
    [
        ("P:Pat1/St1_A", ["P:Pat1/St1_A"]),
        ("P:Pat1/St1*", ["P:Pat1/St1_A"]),
        ("P:Pat1/St1*", ["P:Pat1/St1_A"]),
        ("P:*/*", ["P:Pat1/St1_A", "P:Pat1/St2_B", "P:Pat2/St3_A", "P:Pat2/St4_B"]),
        ("P:*/*B", ["P:Pat1/St2_B", "P:Pat2/St4_B"]),
        ("*", ["P", "Root folder"]),
        ("P:*", ["P:Pat1/St1_A", "P:Pat1/St2_B", "P:Pat2/St3_A", "P:Pat2/St4_B"]),
    ],
)
def test_find(a_runner, tmp_path, query, expected_output):

    # Some mock studies with very short names so checking output is easier
    studies_data = {
        "P": {
            "Pat1": ["St1_A", "St2_B"],
            "Pat2": ["St3_A", "St4_B"],
        },
    }
    a_runner.mock_context._domain = Domain(convert_to_places(studies_data))

    response = a_runner.invoke(find, args=[query], catch_exceptions=False)
    for expected in expected_output:
        assert expected in response.output
    assert response.exit_code == 0
