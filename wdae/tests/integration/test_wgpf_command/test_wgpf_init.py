# pylint: disable=W0621,C0114,C0116,W0212,W0613,C0415,
import pytest

from wdae.wgpf import cli


def test_wgpf_init_simple(wgpf_fixture, wdae_django_setup):
    # Given
    with wdae_django_setup(
            wgpf_fixture,
            "tests.integration.test_wgpf_command.wgpf_settings"):

        assert not (wgpf_fixture.instance_dir / ".wgpf_init.flag").exists()

        # When
        cli(["wgpf", "init", "admin@example.com", "-p", "secret"])

        # Then
        assert (wgpf_fixture.instance_dir / ".wgpf_init.flag").exists()


def test_wgpf_reinit(wgpf_fixture, wdae_django_setup, capsys):
    # Given
    with wdae_django_setup(
            wgpf_fixture,
            "tests.integration.test_wgpf_command.wgpf_settings"):
        cli(["wgpf", "init", "admin@example.com", "-p", "secret"])
        capsys.readouterr()

        # When
        with pytest.raises(SystemExit, match="1"):
            cli(["wgpf", "init", "admin@example.com", "-p", "secret"])

        _out, err = capsys.readouterr()
        assert err.endswith(
            "already initialized. "
            "If you need to re-init please use '--force' flag.\n")


def test_wgpf_force_reinit(wgpf_fixture, wdae_django_setup):
    # Given
    with wdae_django_setup(
            wgpf_fixture,
            "tests.integration.test_wgpf_command.wgpf_settings"):
        cli(["wgpf", "init", "admin@example.com", "-p", "secret"])

        # When
        cli(["wgpf", "init", "--force", "admin@example.com", "-p", "secret"])
