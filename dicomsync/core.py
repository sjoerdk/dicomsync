import fnmatch
from dataclasses import dataclass
from enum import Enum
from itertools import chain
from typing import Any, Dict, Generic, Iterable, List, Tuple, TypeVar, Union
from pydantic import BaseModel

from dicomsync.exceptions import PlaceNotFoundError, StudyNotFoundError
from dicomsync.logs import get_module_logger
from dicomsync.references import LocalStudyQuery, StudyKey, StudyQuery, StudyURI

logger = get_module_logger("core")

# Facilitate type annotation for specialized Place and ImagingStudy types
PlaceType = TypeVar("PlaceType", bound="Place")


@dataclass
class Subject:
    """A person of whom images can be taken. Name is a unique identifier"""

    def __init__(self, name):
        self.name = name

    def __str__(self):
        return f"{self.name}"

    def __eq__(self, other):
        return self.name == other.name


class ImagingStudy(Generic[PlaceType]):
    """The images resulting from a single patient visit. Is always bound to a specific
    Place subtype.

    Responsibilities
    ----------------
    * An ImagingStudy should be unique in the context of a Domain.
    * Acts as a reference, NOT a holder of additional information. Do not add
      fields. Instead, add special functions to Place if needed.
    * Use subtypes to facilitate value annotations. Subtypes are not necessary as
      ImagingStudy has a place field but still clearer to use subtypes I think.

    """

    def __init__(self, subject: Subject, description: str, place: PlaceType):
        self.subject = subject
        self.description = description
        self.place = place

    def __str__(self):
        return f"{self.key()} ({type(self).__name__})"

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
    """Something that contains imaging studies and knows how to handle them.

    Responsibilities
    ----------------
    * A Place instance knows which studies it contains
    * All interactions with contained studies are through key which is a simple string
      Or a LocalStudyQuery, which is basically a parsed string.
    * Place knows how to retrieve a study designated by a key

    Subclassing
    -----------
    * Any child class must implement the _query_studies() method. All other Place
      methods will then work automatically.
    * A child class can offer additional information about studies based on key. The
      information can vary according to Place subtype.
    * To support sending data to a place, implement any of the methods listed in
      routing.SwitchBoard. See Switchboard docstring for reasons.
    * send methods can raise `StudyAlreadyExistsError` if a study that is sent already
      exists.
    """

    def _query_studies(self, query: LocalStudyQuery) -> Iterable[ImagingStudy[Any]]:
        """Return all studies matching to the given query.

        This is the only Place function that needs to be implemented in child classes.

        If nothing is found, returns empty iterable
        """

        raise NotImplementedError()

    def find_duplicates(
        self, studies: List[ImagingStudy[PlaceType]]
    ) -> Tuple[List[ImagingStudy[PlaceType]], List[ImagingStudy[PlaceType]]]:
        """Split off all studies that already exist in this place

        This operation is useful in different places. Opted to define it generally
        here instead of having to re-implement in specific contexts.

        Returns
        -------
        Tuple[List[PlaceType, PlaceType]]
            duplicate studies, non-duplicate studies

        """
        duplicates = []
        non_duplicates = []
        for study in studies:
            if self.contains(study):
                duplicates.append(study)
            else:
                non_duplicates.append(study)
        return duplicates, non_duplicates

    def query_studies(
        self, query: Union[str, LocalStudyQuery]
    ) -> Iterable[ImagingStudy["Place"]]:
        """Return all studies matching to the given query.

        If nothing is found, returns empty iterable

        Allows str as well as LocalStudyQuery object for convenience.

        Raises
        ------
        ValueError
            If query cannot be parsed
        """
        if isinstance(query, str):
            return self._query_studies(query=LocalStudyQuery(key_pattern=query))
        else:
            return self._query_studies(query=query)

    def contains(self, study: ImagingStudy[PlaceType]) -> bool:
        """Return true if this place contains this ImagingStudy"""
        return bool(
            list(self.query_studies(LocalStudyQuery(key_pattern=str(study.key()))))
        )

    def get_study(self, key: StudyKey) -> ImagingStudy[Any]:
        """Return the imaging study corresponding to key.

        Raises
        ------
        StudyNotFoundError
            If study for key is not there
        """
        result: Iterable[ImagingStudy["Place"]]
        result = self.query_studies(LocalStudyQuery(key_pattern=str(key)))
        if not result:
            raise StudyNotFoundError(f"study '{str(key)}' not found")
        return list(result)[0]

    def all_studies(self) -> Iterable[ImagingStudy[Any]]:
        """All studies in this place"""
        return self.query_studies(LocalStudyQuery(key_pattern="*"))


class Domain:
    """A collection of named places.

    The main task of a domain is to associate each Place with a short key (place_key).
    In the context of a domain you can refer to a Place using this key. By
    extension, this means you can use StudyURI strings to uniquely reference any Study
    in a domain.

    Most dicomsync activity takes place within the context of a domain.

    Domain responsibilities:
    * Associate Places with short keys
    * Convert StudyURI to unique Study
    * Resolve StudyQuery by relaying query to the right Place
    * Raising exceptions for unfindable referents.

    Domain does not:
    * Introspect Place. What a Place does is up to the Place. Domain does not know.
    * Instantiate Place. Domains fed fully formed Place instances. No cleverness from
      Domain here.
    * Route. Routing is done outside domain. You just obtain places and studies from
      domain, but any data transfer is initiated outside of domain.
    """

    def __init__(self, places: Dict[str, Place]):
        self.places = places

    def query_studies(
        self, query: Union[str, StudyQuery]
    ) -> Iterable[ImagingStudy[Any]]:

        if isinstance(query, str):
            query_parsed = StudyQuery.init_from_string(query)
        else:
            query_parsed = query

        logger.debug(f"Retrieving all ImagingStudy instances for {query}")
        places = self.query_places(query_parsed.place_pattern).values()
        logger.debug(
            f"Found {(len(places))} places matching place pattern "
            f"'{query_parsed.place_pattern}': {[str(x) for x in places]}"
        )
        return chain(
            *(place.query_studies(query_parsed.key_pattern) for place in places)
        )

    def query_places(self, place_query: str) -> Dict[str, Place]:
        """Find all places matching query"""

        matching = [x for x in fnmatch.filter(self.places.keys(), place_query)]
        return {x: self.places[x] for x in matching}

    def add_place(self, place: Place, key: str):
        """Add place under the given key in this domain.

        Raises
        ------
        KeyError
            if key already exists
        """
        if key in self.places:
            raise KeyError(f"Key '{key}' already exists. I'm not replacing it.")
        else:
            self.places[key] = place

    def get_place(self, place_key: str) -> Place:
        """Get the Place reference by place key from this domain.

        Raises
        ------
        PlaceNotFoundError
            If place is not found by the given name.
        """
        try:
            return self.places[place_key]
        except KeyError as e:
            raise PlaceNotFoundError(
                f'Place "{place_key}" not found. Available '
                f"places: {list(self.places.keys())}"
            ) from e

    def get_key_for_place(self, place: Place):
        """Find the key that the given place is stored under

        Returns
        -------
        Place
            The first place found in settings that matches the given place

        Raises
        ------
        KeyError
            if place is not under any key

        Notes
        -----
        Uses object identity for lookup. Place copy will not yield a result.

        """
        try:
            return next((key for key, x in self.places.items() if x == place))
        except StopIteration as e:
            raise KeyError(
                f"Place not found in settings. Looked for {place} in "
                f"{list(self.places.keys())} but found no match"
            ) from e

    def get_study_uri(self, study: ImagingStudy["Place"]) -> StudyURI:
        """Generate a unique identifier for study in this domain

        Raises
        ------
        KeyError
            if place in study cannot be found in this domain
        """
        return StudyURI(
            place_name=self.get_key_for_place(study.place), study_key=study.key()
        )


class AssertionStatus(str, Enum):
    not_set = "not_set"
    updated = "updated"
    created = "created"
    skipped = "skipped"
    error = "error"


class AssertionResult(BaseModel):
    """When asserting whether study is in a certain state, indicates which actions
    were taken.
    """

    status: AssertionStatus = AssertionStatus.not_set
    message: str = ""
