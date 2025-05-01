from dataclasses import dataclass
from enum import Enum
from typing import Iterable

from pydantic import BaseModel

from dicomsync.exceptions import StudyNotFoundError
from dicomsync.references import LocalStudyQuery, StudyKey


@dataclass
class Subject:
    """A person of whom images can be taken. Name is a unique identifier"""

    def __init__(self, name):
        self.name = name

    def __str__(self):
        return f"{self.name}"

    def __eq__(self, other):
        return self.name == other.name


class ImagingStudy:
    """The images resulting from a single patient visit.

    This could be a CT scan, an X-ray, and MRI scan.
    """

    def __init__(self, subject: Subject, description: str):
        self.subject = subject
        self.description = description

    def key(self) -> StudyKey:
        """Unique identifier referencing this study.

        Notes
        -----
        Lower case keys are expected but not enforced.

        Returns
        -------
        StudyKey
            Unique identifier for this study.

        """
        return StudyKey(patient_name=self.subject.name, study_slug=self.description)


class Place(BaseModel):
    """Can contain imaging studies"""

    # TODO: rewrite all child classes of Place to implement query_studies()

    def query_studies(self, query: LocalStudyQuery) -> Iterable[ImagingStudy]:
        """Return all studies matching to the given query.

        This is the only Place function that needs to be implemented in child classes
        """

        raise NotImplementedError()

    def contains(self, study: ImagingStudy) -> bool:
        """Return true if this place contains this ImagingStudy"""
        return bool(self.query_studies(LocalStudyQuery(key_pattern=str(study.key))))

    def get_study(self, key: StudyKey) -> ImagingStudy:
        """Return the imaging study corresponding to key

        Raises
        ------
        StudyNotFoundError
            If study for key is not there
        """
        result = self.query_studies(LocalStudyQuery(key_pattern=str(key)))
        if not result:
            raise StudyNotFoundError(f"study '{str(key)}' not found")
        return list(result)[0]

    def all_studies(self) -> Iterable[ImagingStudy]:
        """All studies in this place"""
        return self.query_studies(LocalStudyQuery(key_pattern="*"))


class AssertionStatus(str, Enum):
    not_set = "not_set"
    updated = "updated"
    created = "created"
    skipped = "skipped"
    error = "error"


class AssertionResult(BaseModel):
    """When asserting whether study is in a certain state, indicates which actions
    were taken
    """

    status: AssertionStatus = AssertionStatus.not_set
    message: str = ""
