import tempfile
from pathlib import Path
from typing import Any
from unittest.mock import Mock
from uuid import uuid4

import factory

from dicomsync.core import Place, Subject
from dicomsync.filesystem import (
    DICOMRootFolder,
    DICOMStudyFolder,
    ZippedDICOMRootFolder,
    ZippedDICOMStudy,
)
from dicomsync.xnat import XNATUploadedStudy


class SubjectFactory(factory.Factory):
    class Meta:
        model = Subject

    name = factory.sequence(lambda n: f"subject{n}")


class ZippedDICOMStudyFactory(factory.Factory):
    class Meta:
        model = ZippedDICOMStudy

    subject = factory.SubFactory(SubjectFactory)
    description = factory.Sequence(lambda n: f"study{n}")


class XNATUploadedStudyFactory(factory.Factory):
    class Meta:
        model = XNATUploadedStudy

    subject = factory.SubFactory(SubjectFactory)
    description = factory.Sequence(lambda n: f"description_{n}")


class DICOMRootFolderFactory(factory.Factory):
    """DICOM Root Folder with valid but uncreated Path"""

    class Meta:
        model = DICOMRootFolder

    path = factory.LazyFunction(
        lambda: Path(tempfile.gettempdir()) / "dicom_root_folders" / str(uuid4())
    )


class ZippedDICOMRootFolderFactory(factory.Factory):
    """DICOM Root Folder with valid but uncreated Path"""

    class Meta:
        model = ZippedDICOMRootFolder

    path = factory.LazyFunction(
        lambda: Path(tempfile.gettempdir()) / "zipped_dicom_root_folders" / str(uuid4())
    )


class DICOMStudyFolderFactory(factory.Factory):
    class Meta:
        model = DICOMStudyFolder

    subject = factory.SubFactory(SubjectFactory)
    description = factory.Sequence(lambda n: f"studyfolder{n}")
    place = factory.SubFactory(DICOMRootFolderFactory)


def mock_send_methods(place: Place[Any]):
    """Replace the methods that actually send data by mocks. Make sure no data is
    actually sent
    """
    for function_name in ("send_dicom_folder", "send_zipped_study"):
        if hasattr(place, function_name):
            function = getattr(place, function_name)
            setattr(place, function_name, Mock(spec=function))

    return place
