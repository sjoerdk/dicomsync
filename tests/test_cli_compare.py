import shutil
from typing import Any

from dicomsync import cli
from dicomsync.cli.compare import compare
from dicomsync.core import ImagingStudy
from tests.conftest import create_dummy_files
from tests.factories import DICOMStudyFolderFactory


def add_dummy_files(study: ImagingStudy[Any]):
    """Make sure that place has some files on disk corresponding to study.
    For creating dummy data in tests
    """
    study_path = study.place.get_path(study.key())
    study_path.mkdir(parents=True)
    create_dummy_files(study_path, files=3)


class OutputRecorder:
    def __init__(self):
        self.output = []

    def __getitem__(self, idx):
        return self.output[idx]

    def attach(self, func):
        """Attaches this recorder to record all output from func."""

        def new_func(*args, **kwargs):
            returned = func(*args, **kwargs)
            self.output.append(returned)
            return returned

        return new_func

    def clear_output(self):
        self.output = []


def test_compare(a_runner, a_domain, monkeypatch):
    a_runner.mock_context._domain = a_domain

    # add tree studies to place 'a_folder'
    place_a = a_domain.places["a_folder"]
    for _ in range(3):
        add_dummy_files(DICOMStudyFolderFactory(place=place_a))

    # 'compare' output is a long multi-line string. Annoying to assert things about
    #  Create a mock so I can inspect output later
    recorder = OutputRecorder()
    monkeypatch.setattr(
        "dicomsync.cli.compare.find_overlap", recorder.attach(cli.compare.find_overlap)
    )

    # run compare
    response = a_runner.invoke(
        compare,
        args=["a_folder", "a_zip_folder"],
        catch_exceptions=False,
    )
    assert response.exit_code == 0
    # recorder records (in_both, only_in_a, only_in_b). All should be in A only now
    assert tuple(len(x) for x in recorder[-1]) == (0, 3, 0)

    # now copy one study over to b
    place_b = a_domain.places["a_zip_folder"]
    place_b.send_dicom_folder(next(place_a.all_studies()))

    # and run compare again
    response = a_runner.invoke(
        compare, args=["a_folder", "a_zip_folder"], catch_exceptions=False
    )
    assert response.exit_code == 0

    # Now one study should be shared, rest in A
    assert tuple(len(x) for x in recorder[-1]) == (1, 2, 0)

    # Finally, remove the shared study from place_a
    shutil.rmtree(place_a.get_path(next(place_b.all_studies()).key()))
    response = a_runner.invoke(
        compare, args=["a_folder", "a_zip_folder"], catch_exceptions=False
    )
    assert response.exit_code == 0

    # Now one study should be shared, rest in A
    # (in_both, only_in_a, only_in_b)
    assert tuple(len(x) for x in recorder[-1]) == (0, 2, 1)
