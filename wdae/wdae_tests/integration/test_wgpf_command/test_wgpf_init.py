# pylint: disable=W0621,C0114,C0116,W0212,W0613,C0415,
from typing import Callable, ContextManager

import pytest
from gpf_instance.gpf_instance import WGPFInstance

from wdae.wgpf import cli  # type: ignore
from wdae_tests.integration.testing import LiveServer


def test_wgpf_init_simple(
    wgpf_fixture: WGPFInstance,
    wdae_django_setup: Callable[
        [WGPFInstance, str], ContextManager[LiveServer]],
) -> None:
    # Given
    with wdae_django_setup(
            wgpf_fixture,
            "wdae_tests.integration.test_wgpf_command.wgpf_settings"):
        assert not (
            wgpf_fixture.instance_dir / ".wgpf_init.flag"  # type: ignore
        ).exists()

        # When
        cli(["wgpf", "init"])

        # Then
        assert (
            wgpf_fixture.instance_dir / ".wgpf_init.flag"  # type: ignore
        ).exists()


def test_wgpf_reinit(
    wgpf_fixture: WGPFInstance,
    wdae_django_setup: Callable[
        [WGPFInstance, str], ContextManager[LiveServer]],
    capsys: pytest.CaptureFixture,
) -> None:
    # Given
    with wdae_django_setup(
            wgpf_fixture,
            "wdae_tests.integration.test_wgpf_command.wgpf_settings"):
        cli(["wgpf", "init"])
        capsys.readouterr()

        # When
        with pytest.raises(SystemExit, match="0"):
            cli(["wgpf", "init"])

        _out, err = capsys.readouterr()
        assert err.endswith(
            "already initialized. "
            "If you need to re-init please use '--force' flag.\n")


def test_wgpf_force_reinit(
    wgpf_fixture: WGPFInstance,
    wdae_django_setup: Callable[
        [WGPFInstance, str], ContextManager[LiveServer]],
) -> None:
    # Given
    with wdae_django_setup(
            wgpf_fixture,
            "wdae_tests.integration.test_wgpf_command.wgpf_settings"):
        cli(["wgpf", "init"])

        # When
        cli(["wgpf", "init", "--force"])
