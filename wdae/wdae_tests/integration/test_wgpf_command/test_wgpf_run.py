# pylint: disable=W0621,C0114,C0116,W0212,W0613,C0415,

from typing import Callable, ContextManager

import pytest_mock
from gpf_instance.gpf_instance import WGPFInstance

from wdae import wgpf  # type: ignore
from wdae_tests.integration.testing import LiveServer


def test_wgpf_run_simple(
    wgpf_fixture: WGPFInstance,
    wdae_django_setup: Callable[
        [WGPFInstance, str], ContextManager[LiveServer]],
    mocker: pytest_mock.MockerFixture,
) -> None:
    # Given
    with wdae_django_setup(
            wgpf_fixture,
            "wdae_tests.integration.test_wgpf_command.wgpf_settings"):

        (wgpf_fixture.instance_dir / ".wgpf_init.flag").touch()  # type: ignore
        mocker.patch(
            "wdae.wgpf.execute_from_command_line",
            return_value=None)

        # When
        wgpf.cli(["wgpf", "run"])

        # Then
        # pylint: disable=no-member
        wgpf.execute_from_command_line.assert_called_once_with([
            "wgpf", "runserver", "0.0.0.0:8000", "--skip-checks",
        ])


def test_wgpf_run_without_init(
    wgpf_fixture: WGPFInstance,
    wdae_django_setup: Callable[
        [WGPFInstance, str], ContextManager[LiveServer]],
    mocker: pytest_mock.MockerFixture,
) -> None:

    # Given
    with wdae_django_setup(
            wgpf_fixture,
            "wdae_tests.integration.test_wgpf_command.wgpf_settings"):

        mocker.patch(
            "wdae.wgpf.execute_from_command_line",
            return_value=None)

        # When
        wgpf.cli(["wgpf", "run"])

        # Then
        # pylint: disable=no-member
        wgpf.execute_from_command_line.assert_called_with([
            "wgpf", "runserver", "0.0.0.0:8000", "--skip-checks",
        ])

        wgpf.execute_from_command_line.assert_has_calls([
            mocker.call([
                "wgpf", "migrate", "--skip-checks",
            ]),
            mocker.call([
                "wgpf", "createapplication", "public", "authorization-code",
                "--client-id", "gpfjs", "--name", "GPF development server",
                "--redirect-uris", "http://localhost:8000/datasets",
                "--skip-checks",
            ]),
            mocker.call([
                "wgpf", "runserver", "0.0.0.0:8000", "--skip-checks",
            ]),
        ])


def test_wgpf_run_with_port(
    wgpf_fixture: WGPFInstance,
    wdae_django_setup: Callable[
        [WGPFInstance, str], ContextManager[LiveServer]],
    mocker: pytest_mock.MockerFixture,
) -> None:

    # Given
    with wdae_django_setup(
            wgpf_fixture,
            "wdae_tests.integration.test_wgpf_command.wgpf_settings"):

        (wgpf_fixture.instance_dir / ".wgpf_init.flag").touch()  # type: ignore
        mocker.patch(
            "wdae.wgpf.execute_from_command_line",
            return_value=None)

        # When
        wgpf.cli(["wgpf", "run", "-P", "9000"])

        # Then
        # pylint: disable=no-member
        wgpf.execute_from_command_line.assert_called_once_with([
            "wgpf", "runserver", "0.0.0.0:9000", "--skip-checks",
        ])


def test_wgpf_run_with_host(
    wgpf_fixture: WGPFInstance,
    wdae_django_setup: Callable[
        [WGPFInstance, str], ContextManager[LiveServer]],
    mocker: pytest_mock.MockerFixture,
) -> None:

    # Given
    with wdae_django_setup(
            wgpf_fixture,
            "wdae_tests.integration.test_wgpf_command.wgpf_settings"):

        (wgpf_fixture.instance_dir / ".wgpf_init.flag").touch()  # type: ignore
        mocker.patch(
            "wdae.wgpf.execute_from_command_line",
            return_value=None)

        # When
        wgpf.cli(["wgpf", "run", "--host", "localhost"])

        # Then
        # pylint: disable=no-member
        wgpf.execute_from_command_line.assert_called_once_with([
            "wgpf", "runserver", "localhost:8000", "--skip-checks",
        ])


def test_wgpf_run_check_wdae_directory(
    wgpf_fixture: WGPFInstance,
    wdae_django_setup: Callable[
        [WGPFInstance, str], ContextManager[LiveServer]],
    mocker: pytest_mock.MockerFixture,
) -> None:
    # Given
    with wdae_django_setup(
            wgpf_fixture,
            "wdae_tests.integration.test_wgpf_command.wgpf_settings"):

        (wgpf_fixture.instance_dir / ".wgpf_init.flag").touch()  # type: ignore
        mocker.patch(
            "wdae.wgpf.execute_from_command_line",
            return_value=None)

        # When
        wgpf.cli(["wgpf", "run"])

        # Then
        assert (wgpf_fixture.instance_dir / "wdae").exists()  # type: ignore
