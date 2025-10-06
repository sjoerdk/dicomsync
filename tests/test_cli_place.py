from dicomsync.cli.entrypoint import main


def test_no_settings_found(a_runner_with_file, tmp_path):
    # current dir does not contain any settings file
    runner = a_runner_with_file
    runner.mock_context.settings_path = tmp_path / "non-existant"
    response = runner.invoke(main, args=["-v", "place", "list"], catch_exceptions=False)

    # No settings file should show warning message
    assert "No settings" in response.stdout
    assert response.exit_code == 2


def test_place_add_dicom_root(a_runner):
    """Run CLI to add some things and check"""
    places = a_runner.mock_context.get_domain().places
    assert not places
    response = a_runner.invoke(
        main,
        args=["-v", "place", "add", "dicom_root", "key_1", "/a_folder"],
        catch_exceptions=False,
    )
    assert response.exit_code == 0
    assert "key_1" in places


def test_place_add_zip_root(a_runner):
    """Run CLI to add some things and check"""
    places = a_runner.mock_context.get_domain().places
    assert not places
    response = a_runner.invoke(
        main,
        args=["-v", "place", "add", "zipped_root", "key_2", "/a_folder2"],
        catch_exceptions=False,
    )
    assert response.exit_code == 0
    assert "key_2" in places


def test_place_add_xnat_pre_archive(a_runner):
    """Run CLI to add some things and check"""
    places = a_runner.mock_context.get_domain().places
    assert not places
    response = a_runner.invoke(
        main,
        args=[
            "-v",
            "place",
            "add",
            "xnat_pre_archive",
            "key_3",
            "server",
            "project1",
            "a_user",
        ],
        catch_exceptions=False,
    )
    assert response.exit_code == 0
    assert "key_3" in places
    assert places["key_3"].server == "server"
    assert places["key_3"].project_name == "project1"
    assert places["key_3"].user == "a_user"
