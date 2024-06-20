from dataclasses import dataclass
from enum import Enum
from typing import Iterable

from pydantic import BaseModel
from slugify import slugify


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

        Returns
        -------
        str
            Unique identifier for this study.

        """
        raise NotImplementedError()


class Place:
    """Can contain imaging studies"""

    def contains(self, study: ImagingStudy) -> bool:
        """Return true if this place contains this ImagingStudy"""
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
