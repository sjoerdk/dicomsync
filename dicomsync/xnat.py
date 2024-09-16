"""Handles imaging studies in XNAT servers"""
import os
from contextlib import contextmanager
from typing import Any, List, Literal, Optional

import xnat
from xnat.exceptions import XNATUploadError

from dicomsync.core import (
    AssertionResult,
    AssertionStatus,
    ImagingStudy,
    Place,
    Subject,
)
from dicomsync.exceptions import (
    DICOMSyncError,
    PasswordNotFoundError,
    StudyAlreadyExistsError,
    StudyNotFoundError,
)
from dicomsync.local import ZippedDICOMStudy
from dicomsync.logs import get_module_logger

logger = get_module_logger("xnat")


class XNATUploadedStudy(ImagingStudy):
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

    def __init__(self, subject: Subject, description: str):
        super().__init__(subject, description)

    def __str__(self):
        return self.key()


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


class XNATProjectPreArchive(Place):
    """Place where uploaded files end up for an XNAT project. From here, project admins
    can import the files into the XNAT archive proper.

    Notes
    -----
    XNAT project itself is not modelled in dicomsync, as we are only
    interested in uploading studies at the moment. For more functionality interacting
    with xnat projects, use xnat lib.

    You cannot persist a c
    """

    class_name: str = "XNATProjectPreArchive"  # needed for serialization

    connection: Any  # xnat connection object
    project_name: str

    def __str__(self):
        return f"XNATProjectPreArchive '{self.project_name}'"

    def contains(self, study: ImagingStudy) -> bool:
        """Return true if this place contains this ImagingStudy"""
        return study.key() in (x.key() for x in self.all_studies())

    def get_study(self, key: str) -> ImagingStudy:
        """Return the imaging study corresponding to key

        Raises
        ------
        StudyNotFoundError
            If study for key is not there
        """
        study = next((x for x in self.all_studies() if x.key == key), None)
        if not study:
            raise StudyNotFoundError(f"Study '{key}' not found in {self}")
        return study

    def all_studies(self) -> List[XNATUploadedStudy]:
        """Info on studies from XNAT server which are still in pre-archive, awaiting
        import

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
                    subject=subjects[subject_name], description=description
                )
            )
        return studies

    def imported_studies(self) -> List[XNATUploadedStudy]:
        """All studies that have been imported from pre-archive into the project
        itself. You cannot directly import studies here - studies need to be uploaded
        to pre-archive first and then imported from there, usually by a project admin

        Notes
        -----
        I believe that the relation between upload parameters and experiment naming
        in XNAT is arbitrary and might be different for every project or even based
        on human input. Therefore, this method can probably not be relied on.
        Including it here anyway to potentially catch _some_ duplicate uploads
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
                    subject=Subject(name=subject.label), description=item.label
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

    def assert_has_study(self, zipped_study: ZippedDICOMStudy) -> AssertionResult:
        """Make sure the zipped study is in XNAT. If not, upload"""

        previous_studies = self.imported_studies() + self.all_studies()

        if zipped_study.key() in [x.key() for x in previous_studies]:
            logger.info(f"Skipping Study {zipped_study} as it is already in {self}")
            return AssertionResult(status=AssertionStatus.skipped)
        else:
            try:
                self.send_zipped_study(zipped_study)
                return AssertionResult(
                    status=AssertionStatus.created,
                    message=f"created {zipped_study.key()}",
                )
            except DICOMSyncError as e:
                logger.warning(f"Skipping due to Error uploading '{zipped_study}': {e}")
                return AssertionResult(status=AssertionStatus.error, message=str(e))


class SerializableXNATProjectPreArchive(Place):
    """An XNATProjectPreArchive that does not require a logged-in session

    Uses XNATProjectPreArchive internally. Useful for quick loading and saving.
    """

    # needed for pydantic serialization
    type_: Literal[
        "SerializableXNATProjectPreArchive"
    ] = "SerializableXNATProjectPreArchive"

    server: str
    user: str
    project: str

    _pre_archive: Optional[XNATProjectPreArchive] = None

    def get_pre_archive(self) -> XNATProjectPreArchive:
        """

        Raises
        ------
        PasswordNotFoundError
            If password could not be read when initializing connecting to pre_archive
        """
        if not self._pre_archive:
            logger.debug("XNAT pre archive is not initialized yet. Connecting..")
            self._pre_archive = XNATProjectPreArchive(
                connection=xnat.connect(
                    server=self.server,
                    user=self.user,
                    password=self.load_xnat_password(self.user),
                    no_parse_model=False,
                ),
                project_name=self.project,
            )
        return self._pre_archive

    @staticmethod
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

    def contains(self, study: ImagingStudy) -> bool:
        """Return true if this place contains this ImagingStudy"""
        return self.get_pre_archive().contains(study)

    def all_studies(self) -> List[XNATUploadedStudy]:
        """Info on studies from XNAT server which are still in pre-archive, awaiting
        import
        """
        return self.get_pre_archive().all_studies()

    def send_zipped_study(self, zipped_study: ZippedDICOMStudy):
        return self.get_pre_archive().send_zipped_study(zipped_study)
