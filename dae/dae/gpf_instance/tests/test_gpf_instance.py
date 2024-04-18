# pylint: disable=redefined-outer-name,C0114,C0116,protected-access
import os
from typing import Callable

from dae.gpf_instance import GPFInstance


def test_init(fixtures_gpf_instance: GPFInstance) -> None:
    assert fixtures_gpf_instance

    assert fixtures_gpf_instance.dae_config
    print(fixtures_gpf_instance.dae_config)
    assert fixtures_gpf_instance.reference_genome
    assert fixtures_gpf_instance.gene_models
    assert fixtures_gpf_instance._pheno_registry
    assert fixtures_gpf_instance.gene_scores_db is not None
    assert fixtures_gpf_instance.genomic_scores
    assert fixtures_gpf_instance._variants_db
    assert fixtures_gpf_instance.gene_sets_db
    assert fixtures_gpf_instance.denovo_gene_sets_db is not None


def test_eager_init(
    gpf_instance: Callable[[str], GPFInstance],
    global_dae_fixtures_dir: str,
) -> None:
    instance = gpf_instance(
        os.path.join(global_dae_fixtures_dir, "gpf_instance.yaml"))
    instance.load()

    assert instance

    assert instance.dae_config
    assert instance.reference_genome
    assert instance.gene_models
    assert instance._pheno_registry
    assert instance.gene_scores_db is not None
    assert instance.genomic_scores
    assert instance._variants_db
    assert instance.gene_sets_db
    assert instance.denovo_gene_sets_db is not None


def test_dae_config(
    fixtures_gpf_instance: GPFInstance,
    global_dae_fixtures_dir: str,
) -> None:
    dae_config = fixtures_gpf_instance.dae_config

    assert dae_config.conf_dir == global_dae_fixtures_dir


def test_variants_db(
    fixtures_gpf_instance: GPFInstance,
) -> None:
    variants_db = fixtures_gpf_instance._variants_db

    assert len(variants_db.get_all_genotype_data()) == 38
