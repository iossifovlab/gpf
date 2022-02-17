import pytest

import os


def fixtures_dir():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "fixtures"))


@pytest.fixture(scope="function")
def local_gpf_instance(gpf_instance):
    return gpf_instance(fixtures_dir())


def test_init(local_gpf_instance):
    assert local_gpf_instance

    assert local_gpf_instance.dae_config
    print(local_gpf_instance.dae_config)
    assert local_gpf_instance.reference_genome
    assert local_gpf_instance.gene_models
    assert local_gpf_instance._pheno_db
    assert local_gpf_instance._gene_info_config is not None
    assert local_gpf_instance.gene_weights_db is not None
    assert local_gpf_instance._score_config is not None
    assert local_gpf_instance._scores_factory
    assert local_gpf_instance._variants_db
    assert local_gpf_instance.gene_sets_db
    assert local_gpf_instance.denovo_gene_sets_db is not None
    assert local_gpf_instance._background_facade


def test_eager_init(gpf_instance):
    local_gpf_instance = gpf_instance(
        work_dir=None, load_eagerly=True)

    assert local_gpf_instance

    assert local_gpf_instance.dae_config
    assert local_gpf_instance.reference_genome
    assert local_gpf_instance.gene_models
    assert local_gpf_instance._pheno_db
    assert local_gpf_instance._gene_info_config is not None
    assert local_gpf_instance.gene_weights_db is not None
    assert local_gpf_instance._score_config is not None
    assert local_gpf_instance._scores_factory
    assert local_gpf_instance._variants_db
    assert local_gpf_instance.gene_sets_db
    assert local_gpf_instance.denovo_gene_sets_db is not None
    assert local_gpf_instance._background_facade


def test_dae_config(local_gpf_instance):
    dae_config = local_gpf_instance.dae_config

    assert dae_config.dae_data_dir == fixtures_dir()
    assert dae_config.conf_dir == fixtures_dir()


def test_variants_db(local_gpf_instance):
    variants_db = local_gpf_instance._variants_db

    assert len(variants_db.get_all_genotype_data()) == 2
