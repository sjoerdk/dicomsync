"""Functions and Classes to route any type of imaging study to any type of place

Sending an imaging study to a place is sometimes implemented, sometimes not.
Routing logic is done here instead of in each Place definition. Hopefully this is
clearer
"""
from dicomsync.core import ImagingStudy, Place
from dicomsync.exceptions import DICOMSyncError
from dicomsync.local import DICOMStudyFolder, ZippedDICOMStudy


class SwitchBoard:
    """Sends study to a place if possible, raises exceptions if not.

    Knows about all types of studies and types of places.
    """

    # the following methods on a Place indicate being able to handle this type of study
    send_function_names = {
        DICOMStudyFolder: "send_dicom_folder",
        ZippedDICOMStudy: "send_zipped_study",
    }

    def send(self, study: ImagingStudy, place: Place):
        """Send study to place

        Returns
        -------
        None

        Raises
        ------
        SendNotImplementedError
            If sending the study to this place is not possible

        Notes
        -----
        Uses pre-defined send function names to determine whether a place supports
        a certain type of study.

        """
        # find the method to use for this type of study
        method = self.send_function_names.get(type(study))
        if not method:
            raise SendNotImplementedError(
                f"There is no way to send a study of type {type(study)} anywhere"
            )

        # run this method to send study to the place
        try:
            getattr(place, method)(study)
        except AttributeError as e:
            raise SendNotImplementedError(
                f"No method '{type(place).__name__}.{method}()' found. You cannot "
                f"send a study of type {type(study)} to a place of "
                f"type {type(place)}"
            ) from e


class SendNotImplementedError(DICOMSyncError):
    pass
