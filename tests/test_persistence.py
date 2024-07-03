from dicomsync.persistence import DicomSyncSettings


def test_save_load_settings(some_settings):
    """Test basic saving and loading. How to serialize similar sibling classes?"""
    dump = some_settings.model_dump_json()
    loaded = DicomSyncSettings.model_validate_json(dump)
    assert loaded
