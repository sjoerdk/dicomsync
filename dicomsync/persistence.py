"""Functions and classes for handling settings and sensitive data."""
from pathlib import Path
from typing import Any, Dict, Union, cast, get_args

from pydantic import BaseModel

from dicomsync.core import Place
from dicomsync.exceptions import NoSettingsFoundError
from dicomsync.filesystem import DICOMRootFolder, ZippedDICOMRootFolder
from dicomsync.logs import get_module_logger
from dicomsync.xnat import XNATProjectPreArchive

logger = get_module_logger("persistence")

DEFAULT_SETTINGS_FILE_NAME = "dicomsync.json"

# Explicitly list Place[StudyType] subclasses that can be serialized to JSON here.
# Relying on pydantic to infer the classes to instantiat from JSON input when the
# classes themselves use generics is very complicated and hard to debug.
SerializablePlace = Union[DICOMRootFolder, ZippedDICOMRootFolder, XNATProjectPreArchive]


def ensure_serializable(place: Place[Any]) -> SerializablePlace:
    """Raise an exception is this place cannot be serialized by pydantic.

    A place instance does not have to be serializable, but if you want to save it
    to disk it will have to be. This function a stop-gap for the problem
    of inferring types when de-serializing.
    """
    if not isinstance(place, get_args(SerializablePlace)):
        raise ValueError(f"{place} is not a serializable place")
    ser_place = cast(SerializablePlace, place)
    return ser_place


class DicomSyncSettings(BaseModel):
    places: Dict[str, SerializablePlace]

    def save(self):
        """Dummy save to be able to call save on any settings cli"""
        logger.debug("Save() called on non-file settings. Ignoring")


class DicomSyncSettingsFromFile(DicomSyncSettings):
    """Loaded from a path and can be saved to that same path"""

    path: Path

    @classmethod
    def init_from_settings(cls, settings: DicomSyncSettings, path: Path):
        """Convert regular settings into settings from file by adding a path"""
        return cls(**settings.model_dump(), path=path)

    @classmethod
    def init_from_file(cls, file: Path):
        """Load settings from file"""
        try:
            with open(file) as f:
                return cls.init_from_settings(
                    settings=DicomSyncSettings.model_validate_json(f.read()),
                    path=Path(file),
                )
        except FileNotFoundError as e:
            raise NoSettingsFoundError(f"No settings file found at '{file}'") from e

    @staticmethod
    def get_default_file(folder: Path):
        """Get default full path to file given a folder"""
        return folder / DEFAULT_SETTINGS_FILE_NAME

    def save(self):
        with open(self.path, "w") as f:
            # persist super as we don't want to write path into the file
            f.write(super().model_dump_json(indent=2, exclude={"path"}))
