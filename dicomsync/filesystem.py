"""Handling imaging studies on local and network filesystem"""

import shutil
from pathlib import Path
from typing import Any, Iterable, Iterator, List, Literal

from dicomsync.core import (
    ImagingStudy,
    Place,
    Subject,
)
from dicomsync.references import StudyKey, StudyQuery
from dicomsync.exceptions import (
    DICOMSyncError,
    StudyAlreadyExistsError,
    StudyNotFoundError,
)
from dicomsync.logs import get_module_logger

logger = get_module_logger("local")


class DICOMStudyFolder(ImagingStudy["DICOMRootFolder"]):
    """A local folder containing all the DICOM files for a single imaging study."""

    @property
    def path(self) -> Path:
        return self.place.get_path(self.key())

    def all_files(self) -> Iterator[Path]:
        return self.place.all_files(self.key())


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
        etc...
    """

    type_: Literal["DICOMRootFolder"] = "DICOMRootFolder"  # needed for serialization
    path: Path

    def __str__(self):
        return f"Root folder at '{self.path}'"

    def _query_studies(self, query: StudyQuery) -> Iterable[DICOMStudyFolder]:
        """Return all studies matching to the given query"""
        for folder in [
            x
            for x in self.path.glob(query.query_string().replace(":", ""))
            if x.is_dir()
        ]:
            yield DICOMStudyFolder(
                subject=Subject(folder.parent.name),
                description=folder.name,
                place=self,
            )

    def get_path(self, key: StudyKey) -> Path:
        """The location on disk where the files for this study are."""
        return self.path / key.patient_name / key.study_slug

    def all_files(self, key: StudyKey) -> Iterator[Path]:
        return (x for x in self.get_path(key).glob("*") if x.is_file())

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


class ZippedDICOMStudy(ImagingStudy["ZippedDICOMRootFolder"]):
    """A local zipfile containing all the DICOM files for a single imaging study."""

    @property
    def path(self) -> Path:
        return self.place.get_path(self.key())


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
        etc...
    """

    type_: Literal["ZippedDICOMRootFolder"] = "ZippedDICOMRootFolder"

    path: Path

    @classmethod
    def parse_obj(cls, obj):
        return cls._convert_to_real_type_(obj)

    def __str__(self):
        return f"Zipped DICOM Root folder at '{self.path}'"

    def contains(self, study: ImagingStudy[Any]) -> bool:
        """Return true if this place contains this ImagingStudy"""
        return study.key() in (x.key() for x in self.all_studies())

    def get_study(self, key: StudyKey) -> ZippedDICOMStudy:
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
                        place=self,
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

    def get_path(self, key: StudyKey) -> Path:
        """The location on disk corresponding to this study."""

        return self.path / key.patient_name / f"{key.study_slug}.zip"
