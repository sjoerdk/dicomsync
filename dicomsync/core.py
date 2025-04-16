import re
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


def assert_is_valid_slug(string_in):
    """Asserts alphanumeric and undercore. Raises ValueError if not"""

    if not isinstance(string_in, str) or not all(
        c.isalnum() or c == "_" for c in string_in
    ):
        raise ValueError(
            f"Invalid slug: '{string_in}' Only alphanumeric and " f"underscore allowed"
        )


@dataclass
class Subject:
    """A person of whom images can be taken. Name is a unique identifier"""

    def __init__(self, name):
        self.name = name

    def __str__(self):
        return f"{self.name}"

    def __eq__(self, other):
        return self.name == other.name


class StudyKey:
    """Unique identifier for a study in a single place. Format <patient>/<study>"""

    STUDY_SEPARATOR = "/"

    def __init__(self, patient: Subject, study_slug: str):
        self.patient = patient
        self.study_slug = study_slug

    def __str__(self):
        return f"{self.patient.name}{self.STUDY_SEPARATOR}{self.study_slug}"

    def __eq__(self, other):
        return str(other) == str(self)

    @classmethod
    def init_from_string(cls, string_in):
        try:
            patient_name, study_key = string_in.split(cls.STUDY_SEPARATOR)
        except ValueError as e:
            raise DICOMSyncError(f"<patient>{cls.STUDY_SEPARATOR}<study>'") from e
        return cls(
            patient=Subject(name=patient_name),
            study_slug=study_key,
        )

    def to_slug(self) -> "StudyKey":
        """A new identifier where each element has been slugified

        dicomsync internally always uses slug identifiers but the original data might
        not be like that. Sometimes you want to be able to copy-pase a folder name
        with dots as a target.
        """
        return StudyKey(
            patient=self.patient,
            study_slug=make_slug(self.study_slug),
        )


class StudyURI:
    """Unique identifier for a study in any place known to dicomsync.
    Format <Place>:<patient>/<study>

    """

    PLACE_SEPERATOR = ":"

    def __init__(self, place_name: str, study_key: StudyKey):
        self.place_name = place_name
        self.study_key = study_key

    def __str__(self):
        return f"{self.place_name}{self.PLACE_SEPERATOR}{self.study_key}"

    @classmethod
    def init_from_string(cls, string_in):
        try:
            place_name, rest = string_in.split(cls.PLACE_SEPERATOR)
            study_key = StudyKey.init_from_string(rest)
        except ValueError as e:
            raise DICOMSyncError(
                f"Expected format '<place>{cls.PLACE_SEPERATOR}<rest>"
            ) from e
        return cls(
            place_name=place_name,
            study_key=study_key,
        )

    def to_slug(self) -> "StudyURI":
        """A new identifier where each element has been slugified

        dicomsync internally always uses slug identifiers but the original data might
        not be like that. Sometimes you want to be able to copy-pase a folder name
        with dots as a target.
        """
        return StudyURI(
            place_name=make_slug(self.place_name),
            study_key=self.study_key.to_slug(),
        )


class StudyQuery:
    r"""A wildcard-like pattern that can match one or more studies.

    Format <Place>:<patient>/<Key>

    Examples
    --------
    Place1:patient1/key1 -> same as StudyURIParameterType
    Place1:patient1/key* -> list of studies for 'patient1' starting with 'key'
    Place1:patient1/*    -> All studies for 'patient1'
    Place1:patient*      -> All studies for patients starting with 'patient'
    Place1:*             -> All studies for all patients
    Place1               -> All studies for all patients. Same as Place1:*

    Notes
    -----
    Explaining the unreadable regex study format
    "^([\w\*]+):?([\w\*]*)/?([\w\*]*)$"
    > look for any combination of alphanumeric and asterisk [\w\*]*
    > make this a capture group ([\w\*]*)
    > the place and patient separators are optional :? and /?
    > but you do need to match from start ^ to end $

    It really works I promise.
    """

    study_query_format = re.compile(r"^([\w\*]*):?([\w\*]*)/?([\w\*]*)$")

    def __init__(self, place_pattern, key_pattern):
        self.place_pattern = place_pattern
        self.key_pattern = key_pattern

    @classmethod
    def init_from_string(cls, query_string: str):
        parsed = cls.study_query_format.search(query_string)
        if not parsed:
            raise ValueError(
                f"Query '{query_string}' does not seem to be valid. "
                f"Expected format: '<place>:<patient>/<key>' which may "
                f"contain one ore more asterisk (*) as a wildcard"
            )
        (place_pattern, patient_pattern, study_pattern) = parsed.groups()

        return cls(
            place_pattern=place_pattern,
            key_pattern=patient_pattern + "/" + study_pattern,
        )


class ImagingStudy:
    """The images resulting from a single patient visit.

    This could be a CT scan, an X-ray, and MRI scan.
    """

    def __init__(self, subject: Subject, description: str):
        self.subject = subject
        self.description = description

    def key(self) -> StudyKey:
        """Unique identifier. This is used to check whether an imaging study exists
        in a place.

        Notes
        -----
        Lower case keys are expected but not enforced.

        Returns
        -------
        StudyKey
            Unique identifier for this study.

        """
        return StudyKey(
            patient=self.subject,
            study_slug=self.description + "/" + make_slug(self.description),
        )


class Place(BaseModel):
    """Can contain imaging studies"""

    def contains(self, study: ImagingStudy) -> bool:
        """Return true if this place contains this ImagingStudy"""
        raise NotImplementedError()

    def get_study(self, key: StudyKey) -> ImagingStudy:
        """Return the imaging study corresponding to key

        Raises
        ------
        StudyNotFoundError
            If study for key is not there
        """
        raise NotImplementedError()

    def all_studies(self) -> Iterable[ImagingStudy]:
        raise NotImplementedError()

    def query_studies(self, query: StudyQuery) -> Iterable[ImagingStudy]:
        """Return all studies matching to the given query"""

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
