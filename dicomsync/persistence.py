"""Functions and classes for handling settings and sensitive data."""
from pathlib import Path
from typing import Dict, Union

from pydantic import BaseModel

from dicomsync.exceptions import NoSettingsFoundError
from dicomsync.local import DICOMRootFolder, ZippedDICOMRootFolder
from dicomsync.logs import get_module_logger
from dicomsync.xnat import SerializableXNATProjectPreArchive

logger = get_module_logger("persistence")

DEFAULT_SETTINGS_FILE_NAME = "dicomsync.json"

SerializablePlace = (Union)[
    DICOMRootFolder, ZippedDICOMRootFolder, SerializableXNATProjectPreArchive
]


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
        return cls(**settings.dict(), path=path)

    @classmethod
    def init_from_file(cls, file: Path):
        """Load settings from file"""
        try:
            return cls.init_from_settings(
                settings=DicomSyncSettings.parse_file(file), path=file
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
            f.write(super().model_dump_json(indent=2))
