import pytest

import os

from dae.gpf_instance.gpf_instance import GPFInstance


def fixtures_dir():
    return os.path.abspath(
        os.path.join(os.path.dirname(__file__), 'fixtures'))


@pytest.fixture(scope='function')
def gpf_instance(mock_genomes_db):
    return GPFInstance(work_dir=fixtures_dir())


def test_init(gpf_instance):
    assert gpf_instance

    assert gpf_instance.dae_config
    assert gpf_instance.genomes_db
    assert gpf_instance._pheno_db
    assert gpf_instance._gene_info_config
    assert gpf_instance.gene_weights_db is not None
    assert gpf_instance._score_config
    assert gpf_instance._scores_factory
    assert gpf_instance._variants_db
    assert gpf_instance._common_report_facade
    assert gpf_instance.gene_sets_db
    assert gpf_instance.denovo_gene_sets_db is not None
    assert gpf_instance._background_facade


def test_eager_init():
    gpf_instance = GPFInstance(work_dir=fixtures_dir(), load_eagerly=True)
    assert gpf_instance

    assert gpf_instance.dae_config
    assert gpf_instance.genomes_db
    assert gpf_instance._pheno_db
    assert gpf_instance._gene_info_config
    assert gpf_instance.gene_weights_db is not None
    assert gpf_instance._score_config
    assert gpf_instance._scores_factory
    assert gpf_instance._variants_db
    assert gpf_instance._common_report_facade
    assert gpf_instance.gene_sets_db
    assert gpf_instance.denovo_gene_sets_db is not None
    assert gpf_instance._background_facade


def test_dae_config(gpf_instance):
    dae_config = gpf_instance.dae_config

    assert dae_config.dae_data_dir == fixtures_dir()


def test_mocker_genomes_db(gpf_instance):
    genomes_db = gpf_instance.genomes_db

    assert genomes_db.get_genome()
    assert genomes_db.get_genome_from_file()
    assert genomes_db.get_genome_file() == \
        './genomes/GATK_ResourceBundle_5777_b37_phiX174/chrAll.fa'
    assert genomes_db.get_gene_model_id() == 'RefSeq2013'


def test_variants_db(gpf_instance):
    variants_db = gpf_instance._variants_db

    assert len(variants_db.get_all_genotype_data()) == 2
