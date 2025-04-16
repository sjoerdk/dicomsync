from dicomsync.filesystem import ZippedDICOMRootFolder
from dicomsync.persistence import DicomSyncSettings


def test_save_load_settings(some_settings):
    """Test basic saving and loading. How to serialize similar sibling classes?"""
    dump = some_settings.model_dump_json()
    loaded = DicomSyncSettings.model_validate_json(dump)
    for x in some_settings.places.values():
        assert str(x) in [str(y) for y in loaded.places.values()]


def test_child_model_loading():
    """Specific test for the issue of pydantic loading the first matching class instead
    of the actual class. Figuring out how to hint/coerce the right class
    """
    settings = DicomSyncSettings(places={"place1": ZippedDICOMRootFolder(path="path1")})
    dump = settings.model_dump_json()
    loaded = DicomSyncSettings.model_validate_json(dump)

    assert loaded.places["place1"] == settings.places["place1"]
