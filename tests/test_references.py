import pytest

from dicomsync.references import LocalStudyQuery


def test_local_study_query():

    query = LocalStudyQuery.init_from_string(":patient/study")
    assert query.place_pattern == ""
    assert query.key_pattern == "patient/study"

    with pytest.raises(ValueError):
        LocalStudyQuery.init_from_string("a_place:pat/st")
