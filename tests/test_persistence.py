from pathlib import Path

from pytest import fixture

from dicomsync.local import DICOMRootFolder, ZippedDICOMRootFolder
from dicomsync.persistence import DicomSyncSettings
from tests.conftest import create_dummy_files


@fixture
def a_dicom_root_folder(tmpdir):
    folder = Path(tmpdir) / "dicomrootfolder"
    a_study = folder / "patient1" / "study1"
    a_study.mkdir(parents=True)
    create_dummy_files(a_study, files=3)
    return DICOMRootFolder(path=folder)


@fixture
def a_dicom_zipped_folder(tmpdir):
    folder = Path(tmpdir) / "dicomzipfolder"
    a_patient = folder / "patient1"
    a_patient.mkdir(parents=True)
    with open(a_patient / "study1.zip", "w") as f:
        f.write("")
    return ZippedDICOMRootFolder(path=folder)


def test_save_load_settings(a_dicom_root_folder, a_dicom_zipped_folder):
    """Test basic saving and loading. How to serialize similar sibling classes?"""
    settings = DicomSyncSettings(
        places={"placeA": a_dicom_root_folder, "placeB": a_dicom_zipped_folder}
    )

    dump = settings.model_dump_json()
    loaded = DicomSyncSettings.model_validate_json(dump)
    assert loaded
