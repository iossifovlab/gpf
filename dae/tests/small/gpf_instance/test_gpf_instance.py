# pylint: disable=redefined-outer-name,C0114,C0116,protected-access
import pathlib

from dae.gpf_instance import GPFInstance
from dae.testing.setup_helpers import setup_gpf_instance


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
