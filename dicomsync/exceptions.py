class DICOMSyncError(Exception):
    """Base exception for dicomsync"""


class StudyAlreadyExistsError(DICOMSyncError):
    pass


class StudyNotFoundError(DICOMSyncError):
    pass


class NoSettingsFoundError(DICOMSyncError):
    pass


class PasswordNotFoundError(DICOMSyncError):
    pass
