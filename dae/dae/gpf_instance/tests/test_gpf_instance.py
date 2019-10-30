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
    assert gpf_instance.pheno_factory
    assert gpf_instance.gene_info_config
    assert gpf_instance.weights_factory is not None
    assert gpf_instance.score_config
    assert gpf_instance.scores_factory
    assert gpf_instance.variants_db
    assert gpf_instance.common_report_facade
    assert gpf_instance.gene_sets_collections
    assert gpf_instance.denovo_gene_set_facade
    assert gpf_instance.background_facade


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
    variants_db = gpf_instance.variants_db

    assert len(variants_db.get_all()) == 2
