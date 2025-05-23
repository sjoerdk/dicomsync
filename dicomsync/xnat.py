"""Handles imaging studies in XNAT servers"""
import os
import tempfile
from contextlib import contextmanager
from typing import Any, Iterable, List, Literal

import xnat
from xnat import XNATSession
from xnat.exceptions import XNATUploadError

from dicomsync.core import ImagingStudy, Place, Subject
from dicomsync.references import LocalStudyQuery
from dicomsync.exceptions import (
    DICOMSyncError,
    PasswordNotFoundError,
    StudyAlreadyExistsError,
)
from dicomsync.filesystem import (
    DICOMStudyFolder,
    ZippedDICOMRootFolder,
    ZippedDICOMStudy,
)
from dicomsync.logs import get_module_logger

logger = get_module_logger("xnat")


class XNATConnectionFactory:
    """Contains everything to create an xnat connection.

    Use as context manager:

    with XNATConnectionFactory.get_connection() as connection:
        connection.do_a_thing()

    Created this to avoid connection timeouts when performing xnat operations in scripts
    that run several hours/days. I want to set credentials once and then forget about
    them.
    """

    def __init__(self, server, user, password):
        self.server = server
        self.user = user
        self.password = password

    @contextmanager
    def get_connection(self):
        with xnat.connect(
            server=self.server,
            user=self.user,
            password=self.password,
            no_parse_model=False,
        ) as connection:
            yield connection


def load_xnat_password(user):
    """Get XNAT_PASS from environment

    Raises
    ------
    PasswordNotFoundError
    """
    try:
        return os.environ["XNAT_PASS"]
    except KeyError as e:
        raise PasswordNotFoundError(
            f"Cannot get password for user '{user}'. XNAT_PASS not set in"
            f" environment. Use 'export XNAT_PASS=<pass>' to set it"
        ) from e


class XNATProjectPreArchive(Place):
    """Place where uploaded files end up for an XNAT project. From here, project admins
    can import the files into the XNAT archive proper.
    """

    # needed for pydantic serialization
    type_: Literal["XNATProjectPreArchive"] = "XNATProjectPreArchive"

    # xnat connection object.
    # Leading underscore is excluded from pydantic serialization.
    _connection: Any = None

    project_name: str
    server: str
    user: str

    @property
    def connection(self) -> XNATSession:
        """Lazy property that only does expensive initialisation when called"""
        if not self._connection:
            self._connection = self.create_xnat_connection()
        return self._connection

    def create_xnat_connection(self):
        return xnat.connect(
            server=self.server,
            user=self.user,
            password=load_xnat_password(self.user),
            no_parse_model=False,
        )

    def __str__(self):
        return f"XNATProjectPreArchive '{self.project_name}'"

    def contains(self, study: ImagingStudy[Any]) -> bool:
        """Return true if this place contains this ImagingStudy"""
        return study.key() in (x.key() for x in self.all_studies())

    def _query_studies(self, query: LocalStudyQuery) -> Iterable["XNATUploadedStudy"]:
        """Return all studies matching to the given query.

        This is the only Place function that needs to be implemented in child classes.

        If nothing is found, returns empty iterable
        """
        # TODO: make this yield instead of collecting all first
        return self.imported_studies() + self.pre_archive_studies()

    def pre_archive_studies(self) -> List["XNATUploadedStudy"]:
        """Info on studies from XNAT server, which are still in pre-archive awaiting
        import.

        """
        subjects = {}
        studies = []
        for upload_session in self.connection.prearchive.sessions(
            project=self.project_name
        ):
            subject_name = upload_session.subject
            description = upload_session.name

            if subject_name not in subjects:  # avoid duplicate Subject objects
                subjects[subject_name] = Subject(name=subject_name)
            studies.append(
                XNATUploadedStudy(
                    subject=subjects[subject_name], description=description, place=self
                )
            )
        return studies

    def imported_studies(self) -> List["XNATUploadedStudy"]:
        """All studies that have been imported from pre-archive into the project
        itself. You cannot directly import studies here - studies need to be uploaded
        to pre-archive first and then imported from there, usually by a project admin.

        Notes
        -----
        I believe that the relation between upload parameters and experiment naming
        in XNAT is arbitrary and might be different for every project or even based
        on human input. Therefore, this method can probably not be relied on.
        Including it here anyway to potentially catch _some_ duplicate uploads.
        """

        imported_studies = []

        project = self.connection.projects[self.project_name]
        subjects = {x.ID: x for x in project.subjects.tabulate()}
        for item in project.experiments.tabulate(
            columns=("ID", "label", "insert_date", "subject_ID")
        ):

            subject = subjects.get(item.subject_ID)
            if not subject:
                raise DICOMSyncError(
                    f"Experiment referenced an unknown patient. "
                    f"What's going on? Experiment was '{item}'"
                )

            imported_studies.append(
                XNATUploadedStudy(
                    subject=Subject(name=subject.label),
                    description=item.label,
                    place=self,
                )
            )

        return imported_studies

    def send_zipped_study(self, zipped_study: ZippedDICOMStudy):
        logger.info(f"Uploading to {self}: {zipped_study}")
        if self.contains(zipped_study):
            raise StudyAlreadyExistsError(f"Study {zipped_study} is already in {self}")

        logger.info(f"Uploading {zipped_study}")
        try:
            self.connection.services.import_(
                str(zipped_study.path),
                project=self.project_name,
                subject=zipped_study.subject.name,
                experiment=zipped_study.description,
                destination="/prearchive",
            )
        except XNATUploadError as e:
            raise DICOMSyncError(f"Upload failed for '{zipped_study}'") from e
        logger.debug(f"Uploading finished: {zipped_study}")

    def send_dicom_folder(self, folder: DICOMStudyFolder):
        """Zip this folder to temp dir and then send"""
        logger.info(f"Sending {folder} to {self}")
        if self.contains(folder):
            raise StudyAlreadyExistsError(f"Study {folder} is already in {self}")

        with tempfile.TemporaryDirectory() as tmpdir:
            logger.debug(f"zipping to temporary zip location {tmpdir}")
            temp_zipped_root = ZippedDICOMRootFolder(path=tmpdir)
            temp_zipped_root.send_dicom_folder(folder)
            zipped = temp_zipped_root.get_study(folder.key())
            logger.debug("zipping done. On to upload")
            self.send_zipped_study(zipped)
            logger.debug("uploading done. Deleting zip")
            os.remove(zipped.path)


class XNATUploadedStudy(ImagingStudy[XNATProjectPreArchive]):
    """Imaging data related to a single DICOM study

    Notes
    -----
    XNAT uses its own data model which intersects with, but does not fully correspond to
    the DICOM patient>study>series model.
    See https://wiki.xnat.org/documentation/understanding-the-xnat-data-model

    It seems that XNAT allows a lot of flexibility in defining objects but pays for this
    with lack of clarity.

    dicomsync wants clarity, so uses XNATUploadedStudy to mean exactly the data
    belonging to a single study. This means an UploadSession always belongs to a single
    subject and has a single description, which corresponds as much as possible to a
    StudyDescription. 'As much as possible' because XNAT

    In addition, XNAT naming is not consistent. For example. When uploading data to an
    XNAT pre-archive using xnatpy, one can pass the parameter `experiment` which
    internally are converted to a parameter `name` of and UploadSession objects. In
    the XNAT website gui this parameter is then displayed as `Session`.

    This confusion is part of the reason for creating this library
    """
