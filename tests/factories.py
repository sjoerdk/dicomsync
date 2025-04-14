from unittest.mock import Mock

import factory

from dicomsync.core import Place, Subject
from dicomsync.local import DICOMRootFolder, DICOMStudyFolder, ZippedDICOMStudy
from dicomsync.xnat import XNATUploadedStudy


class SubjectFactory(factory.Factory):
    class Meta:
        model = Subject

    name = factory.sequence(lambda n: f"subject{n}")


class DICOMStudyFolderFactory(factory.Factory):
    class Meta:
        model = DICOMStudyFolder

    subject = factory.SubFactory(SubjectFactory)
    description = factory.Sequence(lambda n: f"studyfolder{n}")
    path = factory.Sequence(lambda n: f"path{n}")


class ZippedDICOMStudyFactory(factory.Factory):
    class Meta:
        model = ZippedDICOMStudy

    subject = factory.SubFactory(SubjectFactory)
    description = factory.Sequence(lambda n: f"study{n}")
    path = factory.Sequence(lambda n: f"path{n}")


class XNATUploadedStudyFactory(factory.Factory):
    class Meta:
        model = XNATUploadedStudy

    subject = factory.SubFactory(SubjectFactory)
    description = factory.Sequence(lambda n: f"description_{n}")


class DICOMRootFolderFactory(factory.Factory):
    class Meta:
        model = DICOMRootFolder

    path = factory.Sequence(lambda n: f"path{n}")


def mock_send_methods(place: Place):
    """Replace the methods that actually send data by mocks. Make sure no data is
    actually sent
    """
    for function_name in ("send_dicom_folder", "send_zipped_study"):
        if hasattr(place, function_name):
            function = getattr(place, function_name)
            setattr(place, function_name, Mock(spec=function))

    return place
