"""Test uploading local files to an xnat server"""
from collections import namedtuple
from pathlib import Path
from typing import Any, Iterable, List, Tuple, Union
from unittest.mock import Mock

from _pytest.fixtures import fixture
from xnat import XNATSession
from xnat.mixin import ProjectData
from xnat.prearchive import Prearchive, PrearchiveSession

from dicomsync.core import Domain, Subject
from dicomsync.filesystem import DICOMRootFolder, DICOMStudyFolder
from dicomsync.xnat import XNATProjectPreArchive
from tests.factories import DICOMStudyFolderFactory
from tests.conftest import add_dummy_files


@fixture()
def a_dicom_root_folder(tmpdir):
    root = DICOMRootFolder(path=Path(tmpdir) / "a_dicom_root")

    for _ in range(5):
        study_folder = DICOMStudyFolderFactory(
            place=root,
        )
        add_dummy_files(study_folder)
    return root


def test_basic_upload(a_dicom_root_folder):
    """I have a folder with dicom files. I'd like to upload to xnat"""

    study_folder = DICOMStudyFolder(
        subject=Subject(name="subject1"),
        description="study_1",
        place=a_dicom_root_folder,
    )
    assert study_folder


def test_xnat_place_persistence():
    """An xnat place has an un-persistable XNAT connection property. But still needs
    to be persisted. Also, the password should never be persisted. Make sure this all
    works.
    """

    place = XNATProjectPreArchive(
        project_name="testproject", server="a_server", user="user"
    )
    # Should support model_dump_json
    as_json = place.model_dump_json()

    # And should be re-loadable
    XNATProjectPreArchive.model_validate_json(as_json)


class NameGen:
    """Name generator which allows preset values or else generates defaults"""

    def __init__(self, name, max_items=10, preset_values=None):
        self.name = name
        if preset_values:
            self.generator = iter(preset_values)
        else:
            self.generator = (f"{name}_{i}" for i in range(max_items))

    def __iter__(self):
        return self

    def __next__(self) -> Tuple[str, str]:
        return self.name, next(self.generator)


def create_name_gen(name, max_items=10):
    """Generator for ('name', 'name_x') tuples"""
    print(f"creating name gen with name {name}")
    for i in range(max_items):
        print(f"yielding {name} {i}")
        yield name, f"{name}_{i}"


def create_xnat_response(
    columns: Tuple[Union[str, Tuple[str, Iterable[str]]]], max_items=10
) -> List[Any]:
    """Create the data structure that pyxnat methods often return.

    A tuple of 'TableRow' elements that are namedtuples. The unexpected thing is
    that the `TableRow` datatype varies based on your query. Xnatpy mis-uses the
    namedtuple(name, fields) function here as 'fields' should be a literal and is not
    allowed to be a variable. Python compiles with this, but mypy checking will fail,
    and it's just bad practice to have a 'class' with completely variable fields. It's
    not a class then. Just ignoring this here as this code mimics xnatpy.

    Parameters
    ----------
    columns: Tuple of str or (str,iterable)
        The columns you are asking for. Each column will be a field in all of the
        returned TableRows.
        If a column is a string, TableRows will have that
        string as a field, with consecutively named auto-generated values.
        If a column is a tuple(str, iterable), the values of iterable will be
        used as values of that column.
    max_items: str
        Return at most this many TableRow elements. The number of returned elements
        can be lower if an iterable is passed that runs out sooner.
    """
    column_names = []
    for x in columns:
        if isinstance(x, str):
            column_names.append(x)
        elif isinstance(x, tuple):
            column_names.append(x[0])
        else:
            raise ValueError(f"Invalid input type for columns. " f"Found {type(x)}")

    # mypy ignoring illegal variable class definition.
    TableRow = namedtuple("TableRow", column_names)  # type:ignore[misc]

    # Make sure all columns have a generator.
    generators = {}
    for column in columns:
        if isinstance(column, str):
            column_name = column
            generators[column_name] = NameGen(column_name, max_items=max_items)
        elif isinstance(column, tuple):
            column_name = column[0]
            generators[column_name] = NameGen(
                column_name, max_items=max_items, preset_values=column[1]
            )
        else:
            raise ValueError(
                f"Invalid input type for columns. " f"Found {type(column)}"
            )
    # Run all generators at the same time and create tablerows out of the values.
    # Sorry for this unreadable statement. I'm just generating test data..
    table_params = [dict(list(x)) for x in list(zip(*generators.values(), strict=True))]
    return list(TableRow(**row) for row in table_params)


@fixture
def mock_xnat_session():
    """Pretends to be a connection to an XNAT server (xnat.XNATSession instance)

    This mock was created based on pyxnat with version xnat==0.6.2
    """
    connection = Mock(spec=XNATSession)
    project = Mock(spec=ProjectData)

    patient_ids = [
        f"patient_{x}" for x in range(10)
    ]  # need to correspond so pre-render
    project.subjects = Mock()
    project.subjects.tabulate = lambda: create_xnat_response(
        columns=(("ID", patient_ids), "URI", "label", "insert_date")
    )

    def return_experiments(columns):
        expected = ("ID", "label", "insert_date", "subject_ID")
        if columns != expected:
            raise ValueError(
                f"Columns {columns} are not the expected '{expected}' "
                f"I don't know whether this mock works now"
            )
        return create_xnat_response(
            columns=("ID", "label", "insert_date", ("subject_ID", patient_ids))
        )

    project.experiments.tabulate = return_experiments

    connection.projects = {"test_project": project}

    prearchive = Mock(spec=Prearchive)
    sessions = []
    prearchive.sessions = lambda project: sessions
    for i in range(10):
        session = Mock(spec=PrearchiveSession)
        session.subject = f"subject_{i}"
        session.name = f"session_description_{i}"
        sessions.append(session)

    connection.prearchive = prearchive

    return connection


@fixture
def a_pre_archive(mock_xnat_session):
    """An XNAT project with a mocked XNAT session. Will not connect to any server."""

    place = XNATProjectPreArchive(
        project_name="test_project", server="xnat_server", user="a_user"
    )
    # remove connection function just to be sure. Using __setattr__ because
    # you cannot assign functions directly in a pydantic object
    object.__setattr__(
        place,
        "create_xnat_connection",
        Mock(ide_effect=NotImplementedError("This mock cannot really connect to XNAT")),
    )

    place._connection = mock_xnat_session
    return place


def test_xnat_query(a_pre_archive):
    """Ask an xnat project which studies it contains"""
    place = a_pre_archive
    domain = Domain(places={"pre_archive": place})

    # test different search criteria
    assert len([x for x in domain.query_studies("pre_archive:*")]) == 20
    assert len([x for x in domain.query_studies("pre_archive:label*")]) == 10
    assert len([x for x in domain.query_studies("pre_archive:*7*")]) == 2
    assert len([x for x in domain.query_studies("pre_archive:label_8/*")]) == 1

    # you can also use wildcards in place names
    assert len([x for x in domain.query_studies("pre_arch*:label_8/*")]) == 1
