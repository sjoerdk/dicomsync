import pytest

from dicomsync.core import ImagingStudyIdentifier, Subject, make_slug


@pytest.mark.parametrize("string_in", ["oneword", "an_underscore", "", "234gffj4"])
def test_ensure_slug_works(string_in):

    assert make_slug(string_in) == string_in


@pytest.mark.parametrize("string_in", ["a space", "a-dash", "Capitals", "$#3548"])
def test_ensure_slug_fail(string_in):

    assert not make_slug(string_in) == string_in


def test_study_identifier():

    identifier = ImagingStudyIdentifier(
        place_name="place1", patient=Subject(name="patient1"), study_key="study1"
    )

    assert str(identifier) == "place1:patient1/study1"
    recreated = ImagingStudyIdentifier.init_from_string(str(identifier))
    assert recreated.place_name == "place1"
    assert recreated.patient.name == "patient1"
    assert recreated.study_key == "study1"
