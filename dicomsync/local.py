"""Handling imaging studies on local disks"""
from pathlib import Path
from shutil import copyfile
from typing import List, Union

from dicomsync.core import ImagingStudy, Place, Subject, make_slug


class DICOMStudyFolder(ImagingStudy):
    """A local folder containing all the DICOM files for a single imaging study

    description and subject need to be valid_slugs
    """

    def __init__(self, subject: Subject, description: str, path: Union[Path, str]):
        super().__init__(subject)
        self.description = description
        self.path = Path(path)

    def key(self) -> str:
        return make_slug(f"{self.subject.name}_{self.description}")

    def all_files(self):
        return [x for x in self.path.glob("*") if x.is_file()]

    def __str__(self):
        return f"DICOMStudyFolder {self.subject.name} - {self.description}: {self.path}"


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

    def __init__(self, path: Path):
        self.path = path

    def contains(self, study: ImagingStudy) -> bool:
        """Return true if this place contains this ImagingStudy"""
        return study.key() in (x.key() for x in self.all_studies())

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

        study_path = self.path / folder.subject.name / folder.description

        if study_path.exists():
            if list(study_path.glob("*")):
                raise ValueError(f"{study_path} already exists and is not empty")

        study_path.mkdir(exist_ok=True, parents=True)
        for file in folder.all_files():
            copyfile(file, study_path)
