# pylint: disable=redefined-outer-name,C0114,C0116,protected-access
import pathlib
import textwrap

import pytest

from gpf.gpf_instance import GPFInstance
from gpf.testing.setup_helpers import setup_gpf_instance


def test_init(t4c8_instance: GPFInstance) -> None:
    assert t4c8_instance

    assert t4c8_instance.dae_config
    assert t4c8_instance.reference_genome
    assert t4c8_instance.gene_models
    assert t4c8_instance._pheno_registry
    assert t4c8_instance.gene_scores_db
    assert t4c8_instance.genomic_scores is not None
    assert t4c8_instance._variants_db
    assert t4c8_instance.gene_sets_db is not None
    assert t4c8_instance.denovo_gene_sets_db is not None


def test_dae_config(
    tmp_path: pathlib.Path,
    t4c8_instance: GPFInstance,
) -> None:
    instance = setup_gpf_instance(tmp_path, grr=t4c8_instance.grr)
    assert instance.dae_config.conf_dir == str(tmp_path)


def test_variants_db(t4c8_instance: GPFInstance) -> None:
    variants_db = t4c8_instance._variants_db
    assert len(variants_db.get_all_genotype_data()) == 5


def test_grr_injected_via_kwargs(t4c8_instance: GPFInstance) -> None:
    """GRR passed via constructor kwargs is returned directly."""
    assert t4c8_instance.grr is t4c8_instance._grr


def test_grr_from_config(tmp_path: pathlib.Path) -> None:
    """GRR is built from the grr section in gpf_instance.yaml."""
    grr_dir = tmp_path / "grr"
    grr_dir.mkdir()
    config_path = tmp_path / "gpf_instance.yaml"
    config_path.write_text(textwrap.dedent(f"""\
        instance_id: test_instance
        grr:
          id: config_grr
          type: directory
          directory: {grr_dir}
    """))

    instance = GPFInstance.build(config_path, grr=None)
    grr = instance.grr

    assert grr is not None
    assert grr.repo_id == "config_grr"


def test_grr_from_env_variable(
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """GRR is built from a definition file pointed to by GRR_DEFINITION_FILE."""
    grr_dir = tmp_path / "grr"
    grr_dir.mkdir()
    grr_def_file = tmp_path / "grr_definition.yaml"
    grr_def_file.write_text(textwrap.dedent(f"""\
        id: env_grr
        type: directory
        directory: {grr_dir}
    """))
    monkeypatch.setenv("GRR_DEFINITION_FILE", str(grr_def_file))

    config_path = tmp_path / "gpf_instance.yaml"
    config_path.write_text("instance_id: test_instance\n")

    instance = GPFInstance.build(config_path, grr=None)
    grr = instance.grr

    assert grr is not None
    assert grr.repo_id == "env_grr"


def test_grr_default_definition(
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """When no grr in config or env, fall back to _DEFAULT_GRR_DEFINITION."""
    monkeypatch.delenv("GRR_DEFINITION_FILE", raising=False)
    # Point HOME to tmp_path so ~/.grr_definition.yaml does not exist
    monkeypatch.setenv("HOME", str(tmp_path))

    config_path = tmp_path / "gpf_instance.yaml"
    config_path.write_text("instance_id: test_instance\n")

    instance = GPFInstance.build(config_path, grr=None)
    grr = instance.grr

    assert grr is not None
    assert grr.repo_id == "default_gpf_grr"
