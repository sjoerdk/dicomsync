"""Custom click parameter types"""
from click import ParamType

from dicomsync.cli.base import DicomSyncContext
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


class ImagingStudyParameterType(ParamType):
    """A keyword referencing a single imaging study in a place. Format <Place>/<Key>"""

    name = "imaging_study_key"
    separator = "/"  # between place and key

    def convert(self, value, param, ctx):
        """Try to parse <Place>/<Key>, check whether place exists.

        Returns
        -------
        Place, key
            The Place instance that was saved in settings + imaging study key

        """

        if not value:
            return None  # is default value if parameter not given

        try:
            place_key, study_key = value.split(self.separator)
        except ValueError:
            self.fail(
                message=f'Expected format "place/study", but could not find two'
                f' string separated by "{self.separator}"'
            )
        if not study_key:
            self.fail(message="Study key was empty")

        try:
            return get_place_key(place_key, ctx), study_key
        except PlaceKeyParamError as e:
            self.fail(str(e))

    def __repr__(self):
        return "IMAGING_STUDY_KEY"


class PlaceKeyParamError(DICOMSyncError):
    pass
