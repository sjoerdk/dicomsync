"""Custom click parameter types"""
import re

from click import ParamType

from dicomsync.cli.base import DicomSyncContext
from dicomsync.core import StudyURI
from dicomsync.exceptions import DICOMSyncError


def get_place_key(value, ctx):
    """Try to retrieve a place object for the given key


    Returns
    -------
    Place
        The Place instance for key, from given context
    None
        If value is None (expected for default by ParamType.convert())

    Raises
    ------
    PlaceKeyParamError
        If anything is wrong

    """
    if not value:
        return None  # is default value if parameter not given

    if type(value) is not str:
        raise PlaceKeyParamError(
            f"Expected string input but found {type(value)} " f"value:'{value}'"
        )
    if not isinstance(ctx.obj, DicomSyncContext):
        raise PlaceKeyParamError(
            f"Place Key parameter needs a DicomSyncContext to "
            f"be passed. Found context of type'{type(ctx.obj)}'"
        )

    context: DicomSyncContext = ctx.obj
    settings = context.load_settings()
    try:
        return settings.places[value]
    except KeyError as e:
        raise PlaceKeyParamError(
            f"Could not find '{value}' in places. Choose from "
            f"'{list(settings.places.keys())}'"
        ) from e


class PlaceKeyParameterType(ParamType):
    """A keyword referencing a dicomsync place object in settings"""

    name = "place_key"

    def convert(self, value, param, ctx):
        """Try to read this key from settings

        Returns
        -------
        Place
            The Place instance that was saved in settings

        """
        try:
            return get_place_key(value, ctx)
        except PlaceKeyParamError as e:
            self.fail(str(e))

    def __repr__(self):
        return "PLACE_KEY"


class StudyURIParameterType(ParamType):
    """A keyword referencing a single imaging study in a place.
    Format <Place>:<patient>/<Key>
    """

    name = "study_uri_key"

    def convert(self, value, param, ctx):
        """Try to parse <Place>:<patient>/<Key>, check whether place exists.

        Returns
        -------
        Place, StudyURI
            The Place instance that was saved in settings + imaging study key

        """

        if not value:
            return None  # is default value if parameter not given

        try:
            identifier = StudyURI.init_from_string(value)
        except DICOMSyncError as e:
            self.fail(message=str(e))
        try:
            return get_place_key(identifier.place_name, ctx), identifier
        except PlaceKeyParamError as e:
            self.fail(str(e))

    def __repr__(self):
        return "STUDY_URI_KEY"


class StudyURIQueryParameterType(ParamType):
    """A keyword referencing one or more studies. Can contain wildcards

    Format <Place>:<patient>/<Key>

    Examples
    --------
    Place1:patient1/key1 -> same as StudyURIParameterType
    Place1:patient1/key* -> list of studies for 'patient1' starting with 'key'
    Place1:patient1/*    -> All studies for 'patient1'
    Place1:patient*      -> All studies for patients starting with 'patient'
    Place1:*             -> All studies for all patients
    Place1               -> All studies for all patients. Same as Place1:*

    Returns
    -------
    List[StudyURI]

    Notes
    -----
    When nothing matches, will return empty list, not error.
    """

    name = "study_uri_query"
    study_query_format = re.compile(r"\w+:\w+/\w")

    def convert(self, value, param, ctx):
        """Just validate format <Place>:<patient>/<Key>

        Returns
        -------
        Place, List[StudyURI]
            The Place instance that was saved in settings + imaging study key

        """

        if not value:
            return None  # is default value if parameter not given

        # validate format
        try:
            return StudyURI.init_from_string(value)
        except DICOMSyncError as e:
            self.fail(message=str(e))

    def __repr__(self):
        return "STUDY_URI_QUERY"


class PlaceKeyParamError(DICOMSyncError):
    pass
