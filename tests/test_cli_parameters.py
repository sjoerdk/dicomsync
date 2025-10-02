from dicomsync.cli.click_parameter_types import StudyQueryParameterType


def test_study_query_param_type():
    """Recreates bug with duplicate patient dir"""
    response = StudyQueryParameterType().convert(
        value="place:patient*", param=None, ctx=None
    )
    assert response.key_pattern == "patient*"
    assert response.place_pattern == "place"
