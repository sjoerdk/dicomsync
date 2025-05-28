"""Custom click parameter types"""
import re

from click import ParamType

from dicomsync.logs import get_module_logger
from dicomsync.references import StudyQuery, StudyURI, make_valid_study_query
from dicomsync.exceptions import DICOMSyncError

logger = get_module_logger("cli.click_parameters")


class StudyQueryParameterType(ParamType):
    """A keyword referencing one or more studies. Can contain wildcards.

    Format <Place>:<patient>/<Key>

    Examples
    --------
    Place1:patient1/key1 -> same as StudyURI
    Place1:patient1/key* -> list of studies for 'patient1' starting with 'key'
    Place1:patient1/*    -> All studies for 'patient1'
    Place1:patient*      -> All studies for patients starting with 'patient'
    Place1:*             -> All studies for all patients

    Returns
    -------
    StudyQuery

    """

    name = "study_query"

    def convert(self, value, param, ctx):
        """Just validate format <Place>:<patient>/<Key>

        Returns
        -------
        StudyQuery
        """

        if not value:
            return None  # is default value if parameter not given

        # validate format
        try:
            query = StudyQuery.init_from_string(value)
            query = make_valid_study_query(query)
            return query
        except (DICOMSyncError, ValueError) as e:
            self.fail(message=str(e))

    def __repr__(self):
        return "STUDY_QUERY"


class PlaceQueryParameterType(ParamType):
    """A keyword referencing one or more places

    Examples
    --------
    *               -> List all places
    place*          -> list all places starting with 'place'


    """

    name = "place_query"
    place_query_format = re.compile(r"^[\\*_\w]+$")

    def convert(self, value, param, ctx):
        """Just validate format <Place>:<patient>/<Key>

        Returns
        -------
        string
        """

        if not value:
            return None  # is default value if parameter not given

        # validate format
        if self.place_query_format.search(value):
            return value
        else:
            self.fail(
                message=f"invalid place query string '{value}'. A place query "
                f"should contain only astrerisk *, underscore _, "
                f"letters and numerals"
            )

    def __repr__(self):
        return "PLACE_QUERY"


class QueryParameterType(ParamType):
    """A keyword referencing one or more places or one or more studies.

    Generic query, so I can fold two different functionalities into the 'find' cli
    command:
    1) querying for studies -> 'place:patient/study*'
    2) querying for places ->  '*' or 'place*'

    """

    name = "query"

    def convert(self, value, param, ctx):
        """Just validate format <Place>:<patient>/<Key>

        Returns
        -------
        Union[QueryParameter]


        """
        if StudyURI.PLACE_SEPERATOR in value:
            return StudyQueryParameterType().convert(value, param, ctx)
        else:
            return PlaceQueryParameterType().convert(value, param, ctx)

    def __repr__(self):
        return "QUERY"


class ForcedStudyQueryParameterType(ParamType):
    """StudyQueryParameterType that converts place key to StudyQuery.

    Useful if you want to be sure of a StudyQuery return type and want <place>
    to mean <all studies in place>

    Format <Place>:<patient>/<Key> or just <place>

    Examples
    --------
    Place1:patient1/key1 -> same as StudyURI
    Place1:patient1/key* -> list of studies for 'patient1' starting with 'key'
    Place1:patient1/*    -> All studies for 'patient1'
    Place1:patient*      -> All studies for patients starting with 'patient'
    Place1:*             -> All studies for all patients
    Place1               -> All studies for all patients

    Returns
    -------
    StudyQuery

    """

    name = "study_query"

    def convert(self, value, param, ctx):
        """

        Returns
        -------
        StudyQuery
        """

        if not value:
            return None  # is default value if parameter not given

        # a place like 'place1' is changed to
        if StudyURI.PLACE_SEPERATOR not in value:
            new_value = value + StudyURI.PLACE_SEPERATOR + "*"
            logger.debug(
                f'ForcedStudyQueryParameterType input was place key "{value}"'
                f', adding study wildcard. New value os "{new_value}"'
            )
            value = new_value

        return StudyQueryParameterType().convert(value, param, ctx)

    def __repr__(self):
        return "STUDY_QUERY"


class PlaceKeyParamError(DICOMSyncError):
    pass
