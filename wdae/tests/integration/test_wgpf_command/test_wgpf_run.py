# pylint: disable=W0621,C0114,C0116,W0212,W0613,C0415,
import pytest

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


def test_wgpf_run_without_init(wgpf_fixture, wdae_django_setup, capsys):
    # Given
    with wdae_django_setup(
            wgpf_fixture,
            "tests.integration.test_wgpf_command.wgpf_settings"):
        capsys.readouterr()

        # When / Then
        with pytest.raises(SystemExit, match="1"):
            wgpf.cli(["wgpf", "run"])

        _out, err = capsys.readouterr()
        assert err.endswith(
            " should be initialized first. Run `wgpf init`.\n")


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
