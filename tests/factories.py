import factory

from dicomsync.core import Subject
from dicomsync.local import DICOMStudyFolder


class SubjectFactory(factory.Factory):
    class Meta:
        model = Subject

    name = factory.sequence(lambda n: f"name_{n}")


class DICOMStudyFolderFactory(factory.Factory):
    class Meta:
        model = DICOMStudyFolder

    subject = factory.SubFactory(SubjectFactory)
    description = factory.Sequence(lambda n: f"description_{n}")
    path = factory.Sequence(lambda n: f"path{n}")
