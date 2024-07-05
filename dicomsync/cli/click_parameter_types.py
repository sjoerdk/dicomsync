"""Custom click parameter types"""
from click import ParamType

from dicomsync.cli.base import DicomSyncContext


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
        if not value:
            return None  # is default value if parameter not given

        if type(value) is not str:
            self.fail(
                f"Expected string input but found {type(value)} " f"value:'{value}'"
            )
        if not isinstance(ctx.obj, DicomSyncContext):
            self.fail(
                f"Place Key parameter needs a DicomSyncContext to be passed. "
                f"Found context of type'{type(ctx.obj)}'"
            )

        context: DicomSyncContext = ctx.obj
        settings = context.load_settings()
        try:
            return settings.places[value]
        except KeyError:
            self.fail(
                f"Could not find '{value}' in places. Choose from "
                f"'{list(settings.places.keys())}'"
            )

    def __repr__(self):
        return "PLACE_KEY"
