class DICOMSyncError(Exception):
    """Base exception for dicomsync"""


class StudyAlreadyExistsError(DICOMSyncError):
    pass
