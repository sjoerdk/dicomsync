"""Handles imaging studies in XNAT servers"""
from contextlib import contextmanager
from typing import List

import xnat

from dicomsync.core import ImagingStudy, Place, Subject
from dicomsync.exceptions import StudyAlreadyExistsError
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

    def key(self) -> str:
        """Unique identifier. This is used to check whether an imaging study exists
        in a place.

        Returns
        -------
        str
            Unique identifier for this study.

        """
        return f"{self.subject.name}_{self.description}"

    def __str__(self):
        return self.key()


class XNATSessionFactory:
    """Contains everything to create an xnat connection.

    Use as context manager:

    with XNATSessionFactory.get_session() as connection:
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
    def get_session(self):
        with xnat.connect(
            server=self.server,
            user=self.user,
            password=self.password,
            no_parse_model=False,
        ) as session:
            yield session


class XNATProjectPreArchive(Place):
    """Place where uploaded files end up for an XNAT project. From here, project admins
    can import the files into the XNAT archive proper.

    Notes
    -----
    XNAT project itself is not modelled in dicomsync, as we are only
    interested in uploading studies at the moment. For more functionality interacting
    with xnat projects, use xnat lib.
    """

    def __init__(self, connection, project_name: str):
        """

        Parameters
        ----------
        connection: XNAT connection object
        project_name: str
        """
        self.connection = connection
        self.project_name = project_name

    def contains(self, study: ImagingStudy) -> bool:
        """Return true if this place contains this ImagingStudy"""
        return study.key() in (x.key() for x in self.all_studies())

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
        The XNAT interface does not allow querying for `all studies`. Instead, you have
        to query a `SessionData` class for each image type individually. This is one
        Http get call per query, so it pays to minimize this. Bit weird. Probably discuss
        with xnatpy/xnat devs whether the query 'give me all study information for
        project X' cannot be done in a single query.

        """
        imported_studies = []
        session_data_classes = [
            self.connection.classes.MrSessionData,
            self.connection.classes.CtSessionData,
        ]

        for session_data in session_data_classes:
            logger.debug(f"Querying impored studies of type {session_data}")
            for item in (
                session_data.query(session_data.project == self.project_name)
                .view(
                    session_data.label,
                    session_data.subject_id,
                    session_data.project,
                    self.connection.classes.SubjectData.label,
                )
                .tabulate_dict()
            ):
                imported_studies.append(
                    XNATUploadedStudy(
                        subject=item["xnat_subjectdata_xnat_col_subjectdatalabel"],
                        description=item["xnat_col_mrsessiondatalabel"],
                    )
                )

        return imported_studies

    def send_zipped_study(self, zipped_study: ZippedDICOMStudy):
        if self.contains(zipped_study):
            raise StudyAlreadyExistsError(f"Study {zipped_study} is already in {self}")

        # TODO: Upload this thing and log
