import os
import pytest

from dae.configurable_entities.configuration import ConfigSectionDefinition, \
    DAEConfig


def relative_to_this_test_folder(path):
    return os.path.join(
        os.path.dirname(os.path.realpath(__file__)),
        path
    )


@pytest.fixture
def fixturedir():
    return relative_to_this_test_folder("fixtures")


@pytest.fixture
def dae_config(fixturedir):
    filename = "dae_test.conf"
    config = DAEConfig.make_config(
        dae_data_dir=fixturedir, dae_conf_filename=filename,
        environment_override=False)
    return config


def test_configuration_sections_simple(fixturedir):
    definitions = ConfigSectionDefinition(
        "test_config.conf", work_dir=fixturedir
    )
    assert definitions is not None

    genomes_config = definitions.get_section_config("genomes")
    assert genomes_config is not None

    assert genomes_config.conf_file is not None
    assert "genomes.conf" in genomes_config.conf_file

    assert genomes_config.confFile is not None
    assert "genomes.conf" in genomes_config.confFile

    gene_info = definitions.get_section_config("geneInfo")
    assert gene_info is not None

    assert gene_info.conf_file is not None
    assert "geneInfo.conf" in gene_info.conf_file


def test_dae_config_simple(fixturedir, dae_config):
    assert dae_config is not None

    assert dae_config.dae_data_dir == fixturedir

    assert dae_config.pheno_section() is not None
    print(dae_config.pheno_section())

    assert dae_config.pheno_dir == os.path.join(fixturedir, "pheno")
    assert dae_config.pheno_conf == os.path.join(fixturedir, "phenoDB.conf")

    assert dae_config.gene_info_dir == os.path.join(fixturedir, "geneInfo")
    assert dae_config.gene_info_conf == \
        os.path.join(fixturedir, "geneInfoDB.conf")

    assert dae_config.genomes_dir == \
        os.path.join(fixturedir, "genomes")
    assert dae_config.genomes_conf == \
        os.path.join(fixturedir, "genomesDB.conf")

    assert dae_config.genomic_scores_dir == \
        os.path.join(fixturedir, "genomicScores")
    assert dae_config.genomic_scores_conf == \
        os.path.join(fixturedir, "genomicScores.conf")

    assert dae_config.default_configuration_conf == \
        os.path.join(fixturedir, "defaultConfiguration.conf")


def test_dae_config_genomic_scores_dirs(dae_config):

    assert dae_config.genomic_scores_hg19_dir is not None
    assert os.path.exists(dae_config.genomic_scores_hg19_dir)
    assert os.path.isdir(dae_config.genomic_scores_hg19_dir)

    assert dae_config.genomic_scores_hg38_dir is not None
    assert os.path.exists(dae_config.genomic_scores_hg38_dir)
    assert os.path.isdir(dae_config.genomic_scores_hg38_dir)


def test_dae_config_annotation_defaults(fixturedir, dae_config):
    defaults = dae_config.annotation_defaults
    assert defaults is not None

    assert defaults['wd'] == fixturedir
    assert defaults['data_dir'] == fixturedir
    assert defaults['scores_hg19_dir'] == \
        os.path.join(fixturedir, 'genomic_scores_db')
    assert defaults['scores_hg38_dir'] == \
        os.path.join(fixturedir, 'genomic_scores_db')


def test_dae_config_hdfs(fixturedir, dae_config):
    assert dae_config is not None

    assert dae_config.dae_data_dir == fixturedir

    assert dae_config.hdfs_section() is not None
    print(dae_config.hdfs_section())

    assert dae_config.hdfs_host == 'localhost'
    assert dae_config.hdfs_port == 8020
    assert dae_config.hdfs_base_dir == '/tmp/test_data'


def test_dae_config_override_environment(monkeypatch, fixturedir):
    scores_hg19_dir = os.path.join(fixturedir, 'genomic_scores_db/hg19')
    scores_hg38_dir = os.path.join(fixturedir, 'genomic_scores_db/hg38')

    envs = {
        'DAE_GENOMIC_SCORES_HG19': scores_hg19_dir,
        'DAE_GENOMIC_SCORES_HG38': scores_hg38_dir,
        'DAE_IMPALA_HOST': '127.0.0.1',
        'DAE_IMPALA_PORT': '1024',
        'DAE_IMPALA_DB': 'test-impala-db',
        'DAE_HDFS_HOST': '10.0.0.1',
        'DAE_HDFS_PORT': '2048'
    }
    monkeypatch.setattr(os, 'environ', envs)

    filename = "dae_test.conf"
    config = DAEConfig.make_config(
        dae_data_dir=fixturedir, dae_conf_filename=filename,
        environment_override=True
    )

    assert config.dae_data_dir == fixturedir

    assert config.genomic_scores_hg19_dir == scores_hg19_dir
    assert config.genomic_scores_hg38_dir == scores_hg38_dir
    assert config.impala_host == '127.0.0.1'
    assert config.impala_port == 1024
    assert config.impala_db == 'test-impala-db'
    assert config.hdfs_host == '10.0.0.1'
    assert config.hdfs_port == 2048


def test_dae_config_non_override_environment(monkeypatch, fixturedir):
    scores_dir = os.path.join(fixturedir, 'genomic_scores_db')
    scores_hg19_dir = os.path.join(fixturedir, 'genomic_scores_db/hg19')
    scores_hg38_dir = os.path.join(fixturedir, 'genomic_scores_db/hg38')

    envs = {
        'DAE_GENOMIC_SCORES_HG19': scores_hg19_dir,
        'DAE_GENOMIC_SCORES_HG38': scores_hg38_dir,
        'DAE_IMPALA_HOST': '127.0.0.1',
        'DAE_IMPALA_PORT': '1024',
        'DAE_IMPALA_DB': 'test-impala-db',
        'DAE_HDFS_HOST': '10.0.0.1',
        'DAE_HDFS_PORT': '2048'
    }
    monkeypatch.setattr(os, 'environ', envs)

    filename = "dae_test.conf"
    config = DAEConfig.make_config(
        dae_data_dir=fixturedir, dae_conf_filename=filename,
        environment_override=False
    )

    assert config.dae_data_dir == fixturedir

    assert config.genomic_scores_hg19_dir == scores_dir
    assert config.genomic_scores_hg38_dir == scores_dir
    assert config.impala_host is None
    assert config.impala_port == 21050
    assert config.impala_db == 'gpf_variant_db'
    assert config.hdfs_host == 'localhost'
    assert config.hdfs_port == 8020


def test_dae_config_override_params(fixturedir):
    scores_hg19_dir = os.path.join(fixturedir, 'genomic_scores_db/hg19')
    scores_hg38_dir = os.path.join(fixturedir, 'genomic_scores_db/hg38')
    filename = "dae_test.conf"
    config = DAEConfig.make_config(
        dae_data_dir=fixturedir, dae_conf_filename=filename,
        environment_override=False, dae_scores_hg19_dir=scores_hg19_dir,
        dae_scores_hg38_dir=scores_hg38_dir, impala_host='127.0.0.1',
        impala_port='1024', impala_db='test-impala-db', hdfs_host='10.0.0.1',
        hdfs_port='2048'
    )

    assert config.dae_data_dir == fixturedir

    assert config.genomic_scores_hg19_dir == scores_hg19_dir
    assert config.genomic_scores_hg38_dir == scores_hg38_dir
    assert config.impala_host == '127.0.0.1'
    assert config.impala_port == 1024
    assert config.impala_db == 'test-impala-db'
    assert config.hdfs_host == '10.0.0.1'
    assert config.hdfs_port == 2048


def test_dae_config_override_environment_and_params(monkeypatch, fixturedir):
    scores_hg19_dir = os.path.join(fixturedir, 'genomic_scores_db/hg19')
    scores_hg38_dir = os.path.join(fixturedir, 'genomic_scores_db/hg38')

    envs = {
        'DAE_GENOMIC_SCORES_HG19': 'scores_hg19_dir',
        'DAE_GENOMIC_SCORES_HG38': 'scores_hg38_dir',
        'DAE_IMPALA_HOST': '0.0.0.1',
        'DAE_IMPALA_PORT': '0001',
        'DAE_IMPALA_DB': 'impala-db',
        'DAE_HDFS_HOST': '1.0.0.1',
        'DAE_HDFS_PORT': '0000'
    }
    monkeypatch.setattr(os, 'environ', envs)

    filename = "dae_test.conf"
    config = DAEConfig.make_config(
        dae_data_dir=fixturedir, dae_conf_filename=filename,
        environment_override=True, dae_scores_hg19_dir=scores_hg19_dir,
        dae_scores_hg38_dir=scores_hg38_dir, impala_host='127.0.0.1',
        impala_port='1024', impala_db='test-impala-db', hdfs_host='10.0.0.1',
        hdfs_port='2048'
    )

    assert config.dae_data_dir == fixturedir

    assert config.genomic_scores_hg19_dir == scores_hg19_dir
    assert config.genomic_scores_hg38_dir == scores_hg38_dir
    assert config.impala_host == '127.0.0.1'
    assert config.impala_port == 1024
    assert config.impala_db == 'test-impala-db'
    assert config.hdfs_host == '10.0.0.1'
    assert config.hdfs_port == 2048
