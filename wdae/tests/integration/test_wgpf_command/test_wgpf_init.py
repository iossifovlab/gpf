# pylint: disable=W0621,C0114,C0116,W0212,W0613,C0415,
import textwrap
import pytest

from dae.testing import setup_directories, setup_genome, \
    setup_empty_gene_models

from wdae.wgpf import cli

from ..testing import setup_wgpf_instance


@pytest.fixture
def wgpf_fixture(tmp_path_factory):
    root_path = tmp_path_factory.mktemp("wgpf_command")

    setup_directories(root_path / "gpf_instance", {
        "gpf_instance.yaml": textwrap.dedent("""
        """),
    })
    genome = setup_genome(
        root_path / "alla_gpf" / "genome" / "allChr.fa",
        f"""
        >chrA
        {100 * "A"}
        """
    )
    empty_gene_models = setup_empty_gene_models(
        root_path / "alla_gpf" / "empty_gene_models" / "empty_genes.txt")
    gpf = setup_wgpf_instance(
        root_path / "gpf_instance",
        reference_genome=genome,
        gene_models=empty_gene_models,
    )
    return gpf


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
