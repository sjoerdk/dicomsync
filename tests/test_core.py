import pytest

from dicomsync.core import StudyKey, StudyQuery, StudyURI, Subject, make_slug


@pytest.mark.parametrize("string_in", ["oneword", "an_underscore", "", "234gffj4"])
def test_ensure_slug_works(string_in):

    assert make_slug(string_in) == string_in


@pytest.mark.parametrize("string_in", ["a space", "a-dash", "Capitals", "$#3548"])
def test_ensure_slug_fail(string_in):

    assert not make_slug(string_in) == string_in


def test_study_identifier():

    identifier = StudyURI(
        place_name="place1",
        study_key=StudyKey(patient=Subject(name="patient1"), study_slug="study1"),
    )

    assert str(identifier) == "place1:patient1/study1"
    recreated = StudyURI.init_from_string(str(identifier))
    assert recreated.place_name == "place1"
    assert recreated.study_key.patient.name == "patient1"
    assert recreated.study_key.study_slug == "study1"


class ExpectedError:
    """To indicate expected errors in pytest parametrize"""

    def __init__(self, reason):
        self.reason = reason


@pytest.mark.parametrize(
    ("input_string", "expected_output"),
    [
        ("Pl1:pat1/key", ("Pl1", "pat1", "key")),
        ("Pl1:pat1/k*", ("Pl1", "pat1", "k*")),
        ("Pl1:pat*/k*", ("Pl1", "pat*", "k*")),
        ("Pl1:pat*/", ("Pl1", "pat*", "")),
        ("Pl1:pat*", ("Pl1", "pat*", "")),
        ("Pl1:pat", ("Pl1", "pat", "")),
        ("Pl1:pat:", ExpectedError("Double : not allowed")),
        ("Pl1.", ExpectedError("no dots allowed")),
        ("*:*/key", ("*", "*", "key")),
        (":pat*/*", ("", "pat*", "*")),
        (":pat*//*", ExpectedError("Double slash not allowed")),
        (":/", ("", "", "")),
        (":", ("", "", "")),
        ("/", ("", "", "")),
        ("", ("", "", "")),
        ("*", ("*", "", "")),
        ("**", ("**", "", "")),
        ("Pl1:pat*01*/*", ("Pl1", "pat*01*", "*")),
    ],
)
def test_study_query_regex(input_string, expected_output):
    """Check whether this complicated regex parses the way I expect.

    <Place>:<patient>/<Key>

    Examples
    --------
    Place1:patient1/key1 -> same as StudyURIParameterType
    Place1:patient1/key* -> list of studies for 'patient1' starting with 'key'
    Place1:patient1/*    -> All studies for 'patient1'
    Place1:patient*      -> All studies for patients starting with 'patient'
    Place1:*             -> All studies for all patients
    Place1               -> All studies for all patients. Same as Place1:*
    """

    regex = StudyQuery.study_query_format

    if isinstance(expected_output, ExpectedError):
        output = regex.search(input_string)
        if output:
            raise ValueError(
                f"Input '{input_string}' should not give response, for "
                f"reason '{expected_output.reason}', "
                f"instead, found {output.groups()}"
            )
    else:
        output = regex.search(input_string)
        if not output:
            raise ValueError(
                f"Expected '{input_string}' to be parsed as "
                f"{expected_output}, but found no match for regex {regex}"
            )

        actual_output = regex.search(input_string).groups()
        assert actual_output == expected_output, (
            f"Expected '{input_string}' to be parsed as "
            f"{expected_output}, but found {actual_output} for regex {regex}"
        )
