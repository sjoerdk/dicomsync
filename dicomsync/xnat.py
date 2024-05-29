"""Handles imaging studies in XNAT servers"""
from typing import List

from dicomsync.core import ImagingStudy, Place


class XNATUploadSession(ImagingStudy):
    """Imaging data related to a single DICOM study

    Notes
    -----
    XNAT uses its own data model which intersects with, but does not fully correspond to
    the DICOM patient>study>series model.
    See https://wiki.xnat.org/documentation/understanding-the-xnat-data-model

    It seems that XNAT allows a lot of flexibility in defining objects but pays for this
    with lack of clarity.

    dicomsync wants clarity, so uses XNATUploadSession to mean exactly the data
    belonging to a single study. This means an UploadSession always belongs to a single
    subject and has a single description, which corresponds as much as possible to a
    StudyDescription. 'As much as possible' because XNAT

    In addition, XNAT naming is not consistent. For example. When uploading data to an
    XNAT pre-archive using xnatpy, one can pass the parameter `experiment` which
    internally are converted to a parameter `name` of and UploadSession objects. In
    the XNAT website gui this parameter is then displayed as `Session`.

    This confusion is part of the reason for creating this library
    """

    def __init__(self, subject):
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


class XNATPreArchive(Place):
    """A pre-archive on an XNAT server"""

    def __init__(self, session, project_name: str):
        """

        Parameters
        ----------
        session: Requests.Session
        project_name: str
        """
        self.session = session
        self.project_name = project_name

    @classmethod
    def init_from_credentials(cls, server, user, password, project):
        # TODO
        pass

    def contains(self, study: ImagingStudy) -> bool:
        """Return true if this place contains this ImagingStudy"""
        return study.key() in (x.key() for x in self.all_studies())

    def all_studies(self) -> List[XNATUploadSession]:
        # TODO continue
        _ = self.session.prearchive.sessions()
        return []
