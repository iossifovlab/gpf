
import os

from dae.configuration.config_parser_base import ConfigParserBase


class DAEConfigParser(ConfigParserBase):

    CAST_TO_INT = (
        'port',
    )

    DEFAULT_SECTION_VALUES = {
        'Impala': {
            'db': 'gpf_variant_db',
            'port': '21050'
        }, 'HDFS': {
            'baseDir': '/tmp',
            'port': '0'
        }
    }

    @staticmethod
    def get_environment_override_values():
        impala_db = os.environ.get('DAE_IMPALA_DB', None)
        impala_host = os.environ.get('DAE_IMPALA_HOST', None)
        impala_port = os.environ.get('DAE_IMPALA_PORT', None)
        hdfs_host = os.environ.get('DAE_HDFS_HOST', None)
        hdfs_port = os.environ.get('DAE_HDFS_PORT', None)
        genomic_scores_hg19 = os.environ.get('DAE_GENOMIC_SCORES_HG19', None)
        genomic_scores_hg38 = os.environ.get('DAE_GENOMIC_SCORES_HG38', None)

        environment_override = {}
        if impala_db or impala_host or impala_port:
            environment_override['Impala'] = {}
            if impala_db:
                environment_override['Impala']['db'] = impala_db
            if impala_host:
                environment_override['Impala']['host'] = impala_host
            if impala_port:
                environment_override['Impala']['port'] = impala_port

        if hdfs_host or hdfs_port:
            environment_override['HDFS'] = {}
            if hdfs_host:
                environment_override['HDFS']['host'] = hdfs_host
            if hdfs_port:
                environment_override['HDFS']['port'] = hdfs_port

        if genomic_scores_hg19 or genomic_scores_hg38:
            environment_override['genomicScoresDB'] = {}
            if genomic_scores_hg19:
                environment_override['genomicScoresDB']['scores_hg19_dir'] = \
                    genomic_scores_hg19
            if genomic_scores_hg38:
                environment_override['genomicScoresDB']['scores_hg38_dir'] = \
                    genomic_scores_hg38

        return environment_override

    @classmethod
    def read_and_parse_file_configuration(
            cls, config_file='DAE.conf', work_dir=None, defaults=None,
            environment_override=True):
        if defaults is None:
            defaults = {}

        if work_dir is None:
            work_dir = os.environ.get('DAE_DB_DIR', None)
        assert work_dir is not None
        work_dir = os.path.abspath(work_dir)
        assert os.path.exists(work_dir)
        assert os.path.isdir(work_dir)

        if environment_override:
            override = cls.get_environment_override_values()
            default_override = defaults.get('override', {})
            override.update(default_override)
            defaults['override'] = override

        sections = cls.DEFAULT_SECTION_VALUES
        default_sections = defaults.get('sections', {})
        sections.update(default_sections)
        defaults['sections'] = sections

        config = super(DAEConfigParser, cls).read_file_configuration(
            config_file, work_dir, defaults=defaults
        )

        config = cls.parse(config, dae_data_dir=work_dir)

        return config

    @classmethod
    def parse(cls, config, dae_data_dir=None):
        config = super(DAEConfigParser, cls).parse(config)

        assert config is not None

        if config.genomic_scores_db and \
                config.genomic_scores_db.scores_hg19_dir:
            assert os.path.exists(config.genomic_scores_db.scores_hg19_dir)
            assert os.path.isdir(config.genomic_scores_db.scores_hg19_dir)
        if config.genomic_scores_db and \
                config.genomic_scores_db.scores_hg38_dir:
            assert os.path.exists(config.genomic_scores_db.scores_hg38_dir)
            assert os.path.isdir(config.genomic_scores_db.scores_hg38_dir)

        config['dae_data_dir'] = dae_data_dir
        config['annotation_defaults'] = {
            'wd': config.dae_data_dir,
            'data_dir': config.dae_data_dir,
            'scores_hg19_dir':
                config.genomic_scores_db.scores_hg19_dir
                if config.genomic_scores_db else None,
            'scores_hg38_dir':
                config.genomic_scores_db.scores_hg38_dir
                if config.genomic_scores_db else None,
        }

        return config
