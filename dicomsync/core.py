from dataclasses import dataclass
from typing import Iterable, List

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
    """A person of whom images can be taken"""

    def __init__(self, name):
        self.name = name


class ImagingStudy:
    """The images resulting from a single patient visit.

    This could be a CT scan, an X-ray, and MRI scan.
    """

    def __init__(self, subject: Subject):
        self.subject = subject

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


class SubImage(ImagingStudy):
    pass


class SubPlace(Place):
    def all_studies(self) -> List[SubImage]:
        pass
