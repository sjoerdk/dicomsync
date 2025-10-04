"""Handling imaging studies on local and network filesystem"""
import fnmatch
import shutil
from pathlib import Path
from typing import Iterable, Iterator, Literal

from dicomsync.core import (
    ImagingStudy,
    Place,
    Subject,
)
from dicomsync.references import (
    LocalStudyQuery,
    StudyKey,
    StudyQuery,
    make_valid_study_query,
)
from dicomsync.exceptions import DICOMSyncError, StudyAlreadyExistsError
from dicomsync.logs import get_module_logger

logger = get_module_logger("local")


class DICOMStudyFolder(ImagingStudy["DICOMRootFolder"]):
    """A local folder containing all the DICOM files for a single imaging study."""

    @property
    def path(self) -> Path:
        return self.place.get_path(self.key())

    def all_files(self) -> Iterator[Path]:
        return self.place.all_files(self.key())


class DICOMRootFolder(Place[DICOMStudyFolder]):
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
        """Return all studies matching the given query

        Notes
        -----
        The incoming query is matched fnmatch-style on all length-2 paths relative to
        base path. It is *not* a glob-style match. The two are very similar, but glob
        has undesirable behaviour for patient-name-only wildcards. Specifically,
        for a query like 'patient*' glob will match only the patient folder '/patient1'
        put not the full series path like 'patient1/study1'.
        Query matching is done on the abstract DICOMStudyFolder keys, not on the
        underlying concrete paths.
        """
        # get all patient/study (depth-2) paths.
        study_paths = [x for x in self.path.glob("*/*") if x.is_dir()]

        # match using fnmatch. See Notes above for reasoning.
        query_str = LocalStudyQuery.init_from_study_query(
            make_valid_study_query(query)
        ).query_string()
        matched = [
            x
            for x in study_paths
            if fnmatch.fnmatch(str(x.relative_to(self.path)), query_str)
        ]

        for folder in matched:
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


class ZippedDICOMRootFolder(Place[ZippedDICOMStudy]):
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

    def _query_studies(self, query: LocalStudyQuery) -> Iterable[ZippedDICOMStudy]:
        """Return all zipped studies matching the given query.

        If nothing is found, returns empty iterable
        """
        # collect all files that are 2 deep and point to a file
        candidates = [x for x in self.path.glob("*/*.zip") if (x.is_file())]  # and ]
        matches = [
            x
            for x in candidates
            if fnmatch.fnmatch(
                name=str(x.relative_to(self.path)), pat=query.query_string() + ".zip"
            )
        ]

        for path in matches:
            yield ZippedDICOMStudy(
                subject=Subject(path.parent.name),
                description=path.stem,  # remove .zip extension
                place=self,
            )

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

    def get_study(self, key: StudyKey) -> ZippedDICOMStudy:
        study: ZippedDICOMStudy = super().get_study(key)
        return study
