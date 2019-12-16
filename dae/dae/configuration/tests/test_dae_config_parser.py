import os
import pytest

from dae.configuration.dae_config_parser import DAEConfigParser


def relative_to_this_test_folder(path):
    return os.path.join(
        os.path.dirname(os.path.realpath(__file__)),
        path
    )


@pytest.fixture
def fixturedir():
    return relative_to_this_test_folder('fixtures')


@pytest.fixture
def dae_config(fixturedir):
    filename = 'dae_test.conf'
    config = DAEConfigParser.read_and_parse_file_configuration(
        config_file=filename, work_dir=fixturedir, environment_override=False)
    return config


def test_configuration_sections_simple(fixturedir):
    sections = DAEConfigParser.read_and_parse_file_configuration(
        'test_config.conf',
        fixturedir
    )
    assert sections is not None

    genomes_config = sections.get('genomes')
    assert genomes_config is not None

    assert genomes_config.conf_file is not None
    assert 'genomes.conf' in genomes_config.conf_file

    assert genomes_config.confFile is not None
    assert 'genomes.conf' in genomes_config.confFile

    gene_info = sections.get('geneInfo')
    assert gene_info is not None

    assert gene_info.conf_file is not None
    assert 'geneInfo.conf' in gene_info.conf_file


def test_dae_config_simple(fixturedir, dae_config):
    assert dae_config is not None

    assert dae_config.dae_data_dir == fixturedir

    assert dae_config.studies_db.dir == os.path.join(fixturedir, 'studies')

    assert dae_config.phenotype_data is not None
    print(dae_config.phenotype_data)

    assert dae_config.phenotype_data.dir == os.path.join(fixturedir, 'pheno')

    assert dae_config.gene_info_db.conf_file == \
        os.path.join(fixturedir, 'geneInfoDB.conf')

    assert dae_config.genomes_db.conf_file == \
        os.path.join(fixturedir, 'genomesDB.conf')

    assert dae_config.genomic_scores_db.conf_file == \
        os.path.join(fixturedir, 'genomicScores.conf')

    assert dae_config.default_configuration.conf_file == \
        os.path.join(fixturedir, 'defaultConfiguration.conf')


def test_dae_config_genomic_scores_dirs(dae_config):

    assert dae_config.genomic_scores_db.scores_hg19_dir is not None
    assert os.path.exists(dae_config.genomic_scores_db.scores_hg19_dir)
    assert os.path.isdir(dae_config.genomic_scores_db.scores_hg19_dir)

    assert dae_config.genomic_scores_db.scores_hg38_dir is not None
    assert os.path.exists(dae_config.genomic_scores_db.scores_hg38_dir)
    assert os.path.isdir(dae_config.genomic_scores_db.scores_hg38_dir)


def test_dae_config_annotation_defaults(fixturedir, dae_config):
    defaults = dae_config.annotation_defaults
    assert defaults is not None

    assert defaults['wd'] == fixturedir
    assert defaults['data_dir'] == fixturedir
    assert defaults['scores_hg19_dir'] == \
        os.path.join(fixturedir, 'genomic_scores_db')
    assert defaults['scores_hg38_dir'] == \
        os.path.join(fixturedir, 'genomic_scores_db')


def test_dae_config_genotype_storage(dae_config):
    assert dae_config is not None

    assert len(dae_config.storage) == 3
    assert list(dae_config.storage.keys()) == \
        ['genotype_impala', 'override_impala', 'genotype_filesystem']


def test_dae_config_impala_genotype_storage(dae_config, fixturedir):
    assert dae_config is not None

    assert dae_config.dae_data_dir == fixturedir

    genotype_impala_storage = dae_config.storage.genotype_impala

    assert genotype_impala_storage.id == 'genotype_impala'
    assert genotype_impala_storage.type == 'impala'

    assert genotype_impala_storage.impala.host == 'localhost'
    assert genotype_impala_storage.impala.port == 21050
    assert genotype_impala_storage.impala.db == 'variant_db'

    assert genotype_impala_storage.hdfs is not None
    assert genotype_impala_storage.hdfs.host == 'localhost'
    assert genotype_impala_storage.hdfs.port == 8020
    assert genotype_impala_storage.hdfs.base_dir == '/tmp/test_data'


def test_dae_config_filesystem_genotype_storage(dae_config, fixturedir):
    assert dae_config is not None

    assert dae_config.dae_data_dir == fixturedir

    genotype_filesystem_storage = dae_config.storage.genotype_filesystem

    assert genotype_filesystem_storage.id == 'genotype_filesystem'
    assert genotype_filesystem_storage.type == 'filesystem'
    assert genotype_filesystem_storage.dir == '/tmp/test_data'


def test_dae_config_default_genotype_storage(dae_config, fixturedir):
    assert dae_config is not None

    assert dae_config.genotype_storage.default == 'genotype_filesystem'


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

    filename = 'dae_test.conf'
    config = DAEConfigParser.read_and_parse_file_configuration(
        config_file=filename, work_dir=fixturedir, environment_override=True
    )

    assert config.dae_data_dir == fixturedir

    assert config.genomic_scores_db.scores_hg19_dir == scores_hg19_dir
    assert config.genomic_scores_db.scores_hg38_dir == scores_hg38_dir
    assert config.storage.override_impala.impala.host == '127.0.0.1'
    assert config.storage.override_impala.impala.port == 1024
    assert config.storage.override_impala.impala.db == 'test-impala-db'
    assert config.storage.override_impala.hdfs.host == '10.0.0.1'
    assert config.storage.override_impala.hdfs.port == 2048


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

    filename = 'dae_test.conf'
    config = DAEConfigParser.read_and_parse_file_configuration(
        config_file=filename, work_dir=fixturedir, environment_override=False
    )

    assert config.dae_data_dir == fixturedir

    assert config.genomic_scores_db.scores_hg19_dir == scores_dir
    assert config.genomic_scores_db.scores_hg38_dir == scores_dir
    assert config.storage.override_impala.impala.host is None
    assert config.storage.override_impala.impala.port == 21050
    assert config.storage.override_impala.impala.db == 'gpf_variant_db'
    assert config.storage.override_impala.hdfs.host == 'localhost'
    assert config.storage.override_impala.hdfs.port == 8020


def test_dae_config_override_params(fixturedir):
    scores_hg19_dir = os.path.join(fixturedir, 'genomic_scores_db/hg19')
    scores_hg38_dir = os.path.join(fixturedir, 'genomic_scores_db/hg38')
    filename = 'dae_test.conf'

    default_sections = {
        'impala_storage': {
            'impala': {
                'db': 'test-impala-db',
                'host': '127.0.0.1',
                'port': '1024'
            }, 'hdfs': {
                'host': '10.0.0.1',
                'port': '2048'
            }
        }, 'genomicScoresDB': {
            'scores_hg19_dir': scores_hg19_dir,
            'scores_hg38_dir': scores_hg38_dir
        }
    }

    config = DAEConfigParser.read_and_parse_file_configuration(
        config_file=filename, work_dir=fixturedir,
        defaults={'override': default_sections}, environment_override=False
    )

    assert config.dae_data_dir == fixturedir

    assert config.genomic_scores_db.scores_hg19_dir == scores_hg19_dir
    assert config.genomic_scores_db.scores_hg38_dir == scores_hg38_dir
    assert config.storage.override_impala.impala.host == '127.0.0.1'
    assert config.storage.override_impala.impala.port == 1024
    assert config.storage.override_impala.impala.db == 'test-impala-db'
    assert config.storage.override_impala.hdfs.host == '10.0.0.1'
    assert config.storage.override_impala.hdfs.port == 2048


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

    filename = 'dae_test.conf'

    default_sections = {
        'impala_storage': {
            'impala': {
                'db': 'test-impala-db',
                'host': '127.0.0.1',
                'port': '1024'
            }, 'hdfs': {
                'host': '10.0.0.1',
                'port': '2048'
            }
        }, 'genomicScoresDB': {
            'scores_hg19_dir': scores_hg19_dir,
            'scores_hg38_dir': scores_hg38_dir
        }
    }

    config = DAEConfigParser.read_and_parse_file_configuration(
        config_file=filename, work_dir=fixturedir,
        defaults={'override': default_sections}, environment_override=True
    )

    assert config.dae_data_dir == fixturedir

    assert config.genomic_scores_db.scores_hg19_dir == scores_hg19_dir
    assert config.genomic_scores_db.scores_hg38_dir == scores_hg38_dir
    assert config.storage.override_impala.impala.host == '127.0.0.1'
    assert config.storage.override_impala.impala.port == 1024
    assert config.storage.override_impala.impala.db == 'test-impala-db'
    assert config.storage.override_impala.hdfs.host == '10.0.0.1'
    assert config.storage.override_impala.hdfs.port == 2048


def test_missing_permission_denied_prompt(dae_config):
    assert dae_config.gpfjs.permission_denied_prompt == \
        ('This is a default permission denied prompt.'
         ' Please log in or register.')


def test_permission_denied_prompt_from_file(fixturedir):
    filepath = os.path.join(fixturedir, 'permissionDeniedPrompt.md')

    override = {
        'gpfjs': {
            'permissionDeniedPromptFile': filepath,
        }
    }

    dae_config = DAEConfigParser.read_and_parse_file_configuration(
        config_file='dae_test.conf', work_dir=fixturedir,
        defaults={'override': override}
    )

    assert dae_config.gpfjs.permission_denied_prompt == \
        ('This is a real permission denied prompt.'
         ' The config parser has successfully loaded the file.\n')


def test_permission_denied_prompt_from_nonexistent_file(fixturedir):
    filepath = os.path.join(fixturedir, 'nonExistentFile.someFormat')

    override = {
        'gpfjs': {
            'permissionDeniedPromptFile': filepath,
        }
    }

    with pytest.raises(AssertionError):
        DAEConfigParser.read_and_parse_file_configuration(
            config_file='dae_test.conf', work_dir=fixturedir,
            defaults={'override': override}
        )
