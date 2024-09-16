"""Handling imaging studies on local disks"""
import shutil
from pathlib import Path
from typing import List, Literal, Union

from dicomsync.core import (
    AssertionResult,
    AssertionStatus,
    ImagingStudy,
    Place,
    Subject,
)
from dicomsync.exceptions import (
    DICOMSyncError,
    StudyAlreadyExistsError,
    StudyNotFoundError,
)
from dicomsync.logs import get_module_logger

logger = get_module_logger("local")


class DICOMStudyFolder(ImagingStudy):
    """A local folder containing all the DICOM files for a single imaging study

    description and subject need to be valid_slugs
    """

    def __init__(self, subject: Subject, description: str, path: Union[Path, str]):
        super().__init__(subject, description)
        self.path = Path(path)

    def all_files(self):
        return [x for x in self.path.glob("*") if x.is_file()]

    def __str__(self):
        return f"{self.subject.name} - {self.description}: {self.path}"


class DICOMRootFolder(Place):
    """A folder with patient/study structure.

    Each subfolder represents a patient. In each patient folder there is a folder
    for each study

    base_path/
        subject1/
            study1/
            study2/
        subject2/
            study1/
        etc..
    """

    type_: Literal["DICOMRootFolder"] = "DICOMRootFolder"  # needed for serialization
    path: Path

    def __str__(self):
        return f"Root folder at '{self.path}'"

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
        study = next((x for x in self.all_studies() if x.key() == key), None)
        if not study:
            raise StudyNotFoundError(f"Study '{key}' not found in {self}")
        return study

    def all_studies(self) -> List[DICOMStudyFolder]:
        studies = []
        for folder in [x for x in self.path.glob("*") if x.is_dir()]:
            for subfolder in [x for x in folder.glob("*") if x.is_dir()]:
                studies.append(
                    DICOMStudyFolder(
                        subject=Subject(folder.name),
                        description=subfolder.name,
                        path=subfolder,
                    )
                )

        return studies

    def send_dicom_folder(self, folder: DICOMStudyFolder):
        """Send a DICOMStudyFolder to here"""

        logger.debug(f"Sending {folder} to {self}")
        if not folder.path.exists():
            raise DICOMSyncError(
                f"{folder.path} does not exist. Cannot find data for" f" {folder}"
            )

        study_path = self.path / folder.subject.name / folder.description

        if study_path.exists():
            if list(study_path.glob("*")):
                raise StudyAlreadyExistsError(f"{study_path} exists and is not empty")

        study_path.mkdir(exist_ok=True, parents=True)
        count = 0
        for file in folder.all_files():
            count += 1
            shutil.copyfile(file, study_path / file.name)

        logger.debug(f"copied {count} files to {self}")


class ZippedDICOMStudy(ImagingStudy):
    """A local zipfile containing all the DICOM files for a single imaging study

    description and subject need to be valid slugs
    """

    def __init__(self, subject: Subject, description: str, path: Union[Path, str]):
        super().__init__(subject, description)
        self.path = Path(path)

    def __str__(self):
        return f"ZippedDICOMStudy {self.subject.name} - {self.description}: {self.path}"


class ZippedDICOMRootFolder(Place):
    """A folder patient/study.zip structure.

    Each subfolder represents a patient. In each patient folder there is a zipfile
    for each study

    base_path/
        subject1/
            study1.zip
            study2.zip
        subject2/
            study1.zip
        etc..
    """

    type_: Literal["ZippedDICOMRootFolder"] = "ZippedDICOMRootFolder"

    path: Path

    @classmethod
    def parse_obj(cls, obj):
        return cls._convert_to_real_type_(obj)

    def __str__(self):
        return f"Zipped DICOM Root folder at '{self.path}'"

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
        study = next((x for x in self.all_studies() if x.key() == key), None)
        if not study:
            raise StudyNotFoundError(f"Study '{key}' not found in {self}")
        return study

    def all_studies(self) -> List[ZippedDICOMStudy]:
        studies = []
        for folder in [x for x in self.path.glob("*") if x.is_dir()]:
            for zipfile in [x for x in folder.glob("*.zip") if x.is_file()]:
                studies.append(
                    ZippedDICOMStudy(
                        subject=Subject(folder.name),
                        description=zipfile.stem,  # remove .zip extension
                        path=zipfile,
                    )
                )

        return studies

    def send_dicom_folder(self, folder: DICOMStudyFolder):
        """Zip this DICOMStudyFolder and save here"""

        if not folder.path.exists():
            raise DICOMSyncError(
                f"{folder.path} does not exist. Cannot find data for" f" {folder}"
            )

        zip_path = self.path / folder.subject.name / f"{folder.description}.zip"

        if zip_path.exists():
            raise StudyAlreadyExistsError(
                f"{zip_path} " f"exists. I'm not overwriting this"
            )
        logger.debug(f"Zipping {folder} to {self}")

        zip_path.parent.mkdir(exist_ok=True, parents=True)
        logger.info(f"Creating zip archive for {folder.path} in {zip_path}")
        # Removing suffix here to stop make_archive from adding another '.zip'
        shutil.make_archive(zip_path.with_suffix(""), "zip", folder.path)
        logger.debug("done")

    def assert_has_zip(self, folder: DICOMStudyFolder) -> AssertionResult:
        """Make sure the given dicom study folder has a corresponding zip file"""
        try:
            self.send_dicom_folder(folder)
            return AssertionResult(status=AssertionStatus.created)
        except StudyAlreadyExistsError:
            logger.debug(f"Zip already existed. Skipping '{folder}'")
            return AssertionResult(status=AssertionStatus.skipped)
