"""References to core objects and queries over these references.

Design elements:
    * References and queries are light, only using strings internally
    * Not using core objects themselves, just strings.
    * Why not just strings then? Because I want to model and validate internal
      structure of the strings that are used.
"""

import re
from typing import Tuple

from dicomsync.strings import make_slug
from dicomsync.exceptions import DICOMSyncError


class StudyKey:
    """Unique identifier for a study in a single place. Format <patient>/<study>"""

    STUDY_SEPARATOR = "/"

    def __init__(self, patient_name: str, study_slug: str):
        self.patient_name = patient_name
        self.study_slug = study_slug

    def __str__(self):
        return f"{self.patient_name}{self.STUDY_SEPARATOR}{self.study_slug}"

    def __eq__(self, other):
        return str(other) == str(self)

    @classmethod
    def init_from_string(cls, string_in):
        try:
            patient_name, study_slug = string_in.split(cls.STUDY_SEPARATOR)
        except ValueError as e:
            raise DICOMSyncError(f"<patient>{cls.STUDY_SEPARATOR}<study>'") from e
        return cls(patient_name=patient_name, study_slug=study_slug)

    def to_slug(self) -> "StudyKey":
        """A new identifier where each element has been slugified

        dicomsync internally always uses slug identifiers but the original data might
        not be like that. Sometimes you want to be able to copy-pase a folder name
        with dots as a target.
        """
        return StudyKey(
            patient_name=self.patient_name,
            study_slug=make_slug(self.study_slug),
        )


class StudyURI:
    """Unique identifier for a study in a domain.
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
    r"""A wildcard-like pattern that can match one or more studies globally.

    A StudyURI with potential wildcards.

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
    ^([\w\*#\-_]*):?([\w\*#\-_]*)/?([\w\*#\-_]*)$
    > look for any combination of alphanumeric and asterisk [\w\*]* and hash and dash
    > make this a capture group ([\w\*]*)
    > the place and patient separators are optional :? and /?
    > but you do need to match from start ^ to end $

    It really works, I promise.

    Raises
    ------
    ValueError
        If the input string cannot be parsed in the format defined above.
    """

    study_query_format = re.compile(r"^([\w\*#\-_]*):?([\w\*#\-_]*)/?([\w\*#\-_]*)$")

    def __init__(self, place_pattern: str, key_pattern: str):
        self.place_pattern = place_pattern
        self.key_pattern = key_pattern

    def __str__(self):
        return f"StudyQuery '{self.query_string()}'"

    @classmethod
    def parse_query_string(cls, query_string: str) -> Tuple[str, str, str]:
        """Try to split <place>:<patient>/<study> into its component parts

        Each component might be empty and contain *
        """
        parsed = cls.study_query_format.search(query_string)

        if not parsed:
            raise ValueError(
                f"Query '{query_string}' does not seem to be valid. "
                f"Expected format: '<place>:<patient>/<key>' which may "
                f"contain one ore more asterisk (*) as a wildcard"
            )
        (place_pattern, patient_pattern, study_pattern) = parsed.groups()
        return place_pattern, patient_pattern, study_pattern

    @classmethod
    def init_from_string(cls, query_string: str):
        (place_pattern, patient_pattern, study_pattern) = cls.parse_query_string(
            query_string
        )
        if study_pattern:
            key_pattern = patient_pattern + StudyKey.STUDY_SEPARATOR + study_pattern
        else:
            key_pattern = patient_pattern

        return cls(place_pattern=place_pattern, key_pattern=key_pattern)

    def query_string(self) -> str:
        """Unique string representation of this query

        the following should hold:
        StudyQuery.init_from_string(string).query_string() == string

        """
        if self.key_pattern:
            return self.place_pattern + StudyURI.PLACE_SEPERATOR + self.key_pattern
        else:
            return self.place_pattern


class LocalStudyQuery(StudyQuery):
    """A StudyQuery that has an empty <place>. For searching within places

    Format <patient>/<Key>
    """

    def __init__(self, key_pattern: str):
        super().__init__(place_pattern="", key_pattern=key_pattern)

    @classmethod
    def init_from_string(cls, query_string: str) -> "LocalStudyQuery":
        (place_pattern, patient_pattern, study_pattern) = cls.parse_query_string(
            query_string
        )
        if place_pattern:
            raise ValueError(
                f"Place in a LocalStudyQuery should be empty, but "
                f"found '{place_pattern}'"
            )
        return cls(
            key_pattern=patient_pattern + StudyKey.STUDY_SEPARATOR + study_pattern
        )

    @classmethod
    def init_from_study_query(cls, study_query: StudyQuery):
        """Create from StudyQuery, removing the place identifier."""
        return cls(key_pattern=study_query.key_pattern)
