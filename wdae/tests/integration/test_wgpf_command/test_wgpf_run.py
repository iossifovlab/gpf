# pylint: disable=W0621,C0114,C0116,W0212,W0613,C0415,

from wdae import wgpf


def test_wgpf_run_simple(wgpf_fixture, wdae_django_setup, mocker):
    # Given
    with wdae_django_setup(
            wgpf_fixture,
            "tests.integration.test_wgpf_command.wgpf_settings"):

        (wgpf_fixture.instance_dir / ".wgpf_init.flag").touch()
        mocker.patch(
            "wdae.wgpf.execute_from_command_line",
            return_value=None)

        # When
        wgpf.cli(["wgpf", "run"])

        # Then
        # pylint: disable=no-member
        wgpf.execute_from_command_line.assert_called_once_with([
            "wgpf", "runserver", "0.0.0.0:8000", "--skip-checks",
            "--settings", "tests.integration.test_wgpf_command.wgpf_settings"])


def test_wgpf_run_without_init(wgpf_fixture, wdae_django_setup, mocker):
    # Given
    with wdae_django_setup(
            wgpf_fixture,
            "tests.integration.test_wgpf_command.wgpf_settings"):

        mocker.patch(
            "wdae.wgpf.execute_from_command_line",
            return_value=None)

        # When
        wgpf.cli(["wgpf", "run"])

        # Then
        # pylint: disable=no-member
        wgpf.execute_from_command_line.assert_called_with([
            "wgpf", "runserver", "0.0.0.0:8000", "--skip-checks",
            "--settings", "tests.integration.test_wgpf_command.wgpf_settings"])

        wgpf.execute_from_command_line.assert_has_calls([
            mocker.call([
                "wgpf", "migrate", "--skip-checks", "--settings",
                "tests.integration.test_wgpf_command.wgpf_settings"]),
            mocker.call([
                "wgpf", "createapplication", "public", "authorization-code",
                "--client-id", "gpfjs", "--name", "GPF development server",
                "--redirect-uris", "http://localhost:8000/datasets",
                "--skip-checks", "--settings",
                "tests.integration.test_wgpf_command.wgpf_settings"]),
            mocker.call([
                "wgpf", "runserver", "0.0.0.0:8000", "--skip-checks",
                "--settings",
                "tests.integration.test_wgpf_command.wgpf_settings"])
        ])


def test_wgpf_run_with_port(wgpf_fixture, wdae_django_setup, mocker):
    # Given
    with wdae_django_setup(
            wgpf_fixture,
            "tests.integration.test_wgpf_command.wgpf_settings"):

        (wgpf_fixture.instance_dir / ".wgpf_init.flag").touch()
        mocker.patch(
            "wdae.wgpf.execute_from_command_line",
            return_value=None)

        # When
        wgpf.cli(["wgpf", "run", "-P", "9000"])

        # Then
        # pylint: disable=no-member
        wgpf.execute_from_command_line.assert_called_once_with([
            "wgpf", "runserver", "0.0.0.0:9000", "--skip-checks",
            "--settings", "tests.integration.test_wgpf_command.wgpf_settings"])


def test_wgpf_run_with_host(wgpf_fixture, wdae_django_setup, mocker):
    # Given
    with wdae_django_setup(
            wgpf_fixture,
            "tests.integration.test_wgpf_command.wgpf_settings"):

        (wgpf_fixture.instance_dir / ".wgpf_init.flag").touch()
        mocker.patch(
            "wdae.wgpf.execute_from_command_line",
            return_value=None)

        # When
        wgpf.cli(["wgpf", "run", "--host", "localhost"])

        # Then
        # pylint: disable=no-member
        wgpf.execute_from_command_line.assert_called_once_with([
            "wgpf", "runserver", "localhost:8000", "--skip-checks",
            "--settings", "tests.integration.test_wgpf_command.wgpf_settings"])
