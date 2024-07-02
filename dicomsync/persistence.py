"""Functions and classes for handling settings and sensitive data."""
from typing import Dict, Union

from pydantic import BaseModel

from dicomsync.local import DICOMRootFolder, ZippedDICOMRootFolder
from dicomsync.logs import get_module_logger
from dicomsync.xnat import XNATProjectPreArchive

logger = get_module_logger("persistence")

SerializablePlace = Union[DICOMRootFolder, ZippedDICOMRootFolder, XNATProjectPreArchive]


class DicomSyncSettings(BaseModel):
    places: Dict[str, SerializablePlace]
