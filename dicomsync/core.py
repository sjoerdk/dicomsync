from dataclasses import dataclass
from enum import Enum
from typing import Iterable

from pydantic import BaseModel
from slugify import slugify

from dicomsync.exceptions import DICOMSyncError


def make_slug(string_in: str) -> str:
    """Make sure the string is a valid slug, usable in a URL or path.
     Uses underscore seperator.

    Returns
    -------
    str Input unchanged

    Raises
    ------
    ValueError
        If string_in is not a valid slug
    """
    response: str = slugify(string_in, separator="_", lowercase=True)

    return response


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

    def key(self) -> str:
        """Unique identifier. This is used to check whether an imaging study exists
        in a place.

        Notes
        -----
        Lower case keys are expected but not enforced.

        Returns
        -------
        str
            Unique identifier for this study.

        """
        return make_slug(self.subject.name) + "/" + make_slug(self.description)


class ImagingStudyIdentifier:
    """Unique identifier for a study in dicomsync. Place:patient/study

    Can be represented as a single string
    """

    PLACE_SEPERATOR = ":"
    STUDY_SEPARATOR = "/"

    def __init__(self, place_name: str, patient: Subject, study_key: str):
        self.place_name = place_name
        self.patient = patient
        self.study_key = study_key

    def __str__(self):
        return (
            f"{self.place_name}{self.PLACE_SEPERATOR}{self.patient.name}"
            f"{self.STUDY_SEPARATOR}{self.study_key}"
        )

    @classmethod
    def init_from_string(cls, string_in):
        try:
            place_name, rest = string_in.split(cls.PLACE_SEPERATOR)
            patient_name, study_key = rest.split(cls.STUDY_SEPARATOR)
        except ValueError as e:
            raise DICOMSyncError(
                f"Expected format '<place>{cls.PLACE_SEPERATOR}"
                f"<patient>{cls.STUDY_SEPARATOR}<study>'"
            ) from e
        return cls(
            place_name=place_name,
            patient=Subject(name=patient_name),
            study_key=study_key,
        )

    def as_study_key(self) -> str:
        """Key for study part only, without place"""
        return f"{self.patient.name}{self.STUDY_SEPARATOR}{self.study_key}"

    def to_slug(self) -> "ImagingStudyIdentifier":
        """A new identifier where each element has been slugified

        dicomsync internally always uses slug identifiers but the original data might
        not be like that. Sometimes you want to be able to copy-pase a folder name
        with dots as a target.
        """
        return ImagingStudyIdentifier(
            place_name=make_slug(self.place_name),
            patient=self.patient,
            study_key=make_slug(self.study_key),
        )


class Place(BaseModel):
    """Can contain imaging studies"""

    def contains(self, study: ImagingStudy) -> bool:
        """Return true if this place contains this ImagingStudy"""
        raise NotImplementedError()

    def get_study(self, key: str) -> ImagingStudy:
        """Return the imaging study corresponding to key

        Raises
        ------
        StudyNotFoundError
            If study for key is not there
        """
        raise NotImplementedError()

    def all_studies(self) -> Iterable[ImagingStudy]:
        raise NotImplementedError()


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
