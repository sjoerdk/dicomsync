"""Handles imaging studies in XNAT servers"""
from contextlib import contextmanager
from datetime import datetime
from typing import List

import xnat

from dicomsync.core import ImagingStudy, Place, Subject


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

    def __init__(self, subject: Subject, description: str, date_uploaded: datetime):
        super().__init__(subject, description)
        self.date_uploaded = date_uploaded

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
    """Contains everything to create an xnat session.

    Use as context manager:

    with XNATSessionFactory.get_session() as session:
        session.do_a_thing()

    Created this to avoid session timeouts when performing xnat operations in scripts
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

    def __init__(self, session, project_name: str):
        """

        Parameters
        ----------
        session: XNAT session object
        project_name: str
        """
        self.session = session
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
        for upload_session in self.session.prearchive.sessions(
            project=self.project_name
        ):
            subject_name = upload_session.subject
            description = upload_session.name

            if subject_name not in subjects:  # avoid duplicate Subject objects
                subjects[subject_name] = Subject(name=subject_name)
            studies.append(
                XNATUploadedStudy(
                    subject=subjects[subject_name],
                    description=description,
                    date_uploaded=upload_session.uploaded,
                )
            )
        return studies
