import os

from dae.configuration.config_parser_base import ConfigParserBase

from dae.utils.dict_utils import recursive_dict_update


class DAEConfigParser(ConfigParserBase):
    '''
    DAEConfigParser is responsible for parsing :ref:`DAE Configuration
    <dae_configuration>`. It inherits
    :class:`ConfigParserBase <dae.configuration.config_parser_base.ConfigParserBase>` and use some
    of its methods for reading and parsing configuration.
    '''

    CAST_TO_INT = (
        'port',
    )

    DEFAULT_VALUES = {
        'impala.db': 'gpf_variant_db',
        'impala.port': '21050',
        'hdfs.base_dir': '/tmp',
        'hdfs.port': '0',
        'dir': '%(wd)s/studies'
    }
    '''
    Holds a  a mapping of property to a value of this property. This mapping
    will be used as default values for the configuration sections.
    '''

    DEFAULT_SECTION_VALUES = {
        'gpfjs': {
            'permissionDeniedPrompt': ('This is a default permission denied'
                                       ' prompt. Please log in or register.')
        },
    }
    '''
    Holds a mapping of configuration section to a mapping of section property
    to a value of this property. This mapping will be used as default values
    for the configuration sections.
    '''

    FILTER_SELECTORS = {
        'storage': None,
    }

    @staticmethod
    def _get_environment_override_values():
        impala_db = os.environ.get('DAE_IMPALA_DB', None)
        impala_host = os.environ.get('DAE_IMPALA_HOST', None)
        impala_port = os.environ.get('DAE_IMPALA_PORT', None)
        hdfs_host = os.environ.get('DAE_HDFS_HOST', None)
        hdfs_port = os.environ.get('DAE_HDFS_PORT', None)
        genomic_scores_hg19 = os.environ.get('DAE_GENOMIC_SCORES_HG19', None)
        genomic_scores_hg38 = os.environ.get('DAE_GENOMIC_SCORES_HG38', None)

        environment_override = {}
        if impala_db or impala_host or impala_port:
            if 'impala_storage' not in environment_override:
                environment_override['impala_storage'] = {}
            if 'impala' not in environment_override['impala_storage']:
                environment_override['impala_storage']['impala'] = {}

            if impala_db:
                environment_override['impala_storage']['impala']['db'] = \
                    impala_db
            if impala_host:
                environment_override['impala_storage']['impala']['host'] = \
                    impala_host
            if impala_port:
                environment_override['impala_storage']['impala']['port'] = \
                    impala_port

        if hdfs_host or hdfs_port:
            if 'impala_storage' not in environment_override:
                environment_override['impala_storage'] = {}
            if 'hdfs' not in environment_override['impala_storage']:
                environment_override['impala_storage']['hdfs'] = {}

            if hdfs_host:
                environment_override['impala_storage']['hdfs']['host'] = \
                    hdfs_host
            if hdfs_port:
                environment_override['impala_storage']['hdfs']['port'] = \
                    hdfs_port

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
    def _get_defaults(cls, environment_override, defaults=None):
        if defaults is None:
            defaults = {}

        if environment_override:
            override = cls._get_environment_override_values()
            default_override = defaults.get('override', {})
            override = recursive_dict_update(override, default_override)
            defaults['override'] = override

        values = cls.DEFAULT_VALUES
        default_values = defaults.get('values', {})
        values = recursive_dict_update(values, default_values)
        defaults['values'] = values

        sections = cls.DEFAULT_SECTION_VALUES
        default_sections = defaults.get('sections', {})
        sections = recursive_dict_update(sections, default_sections)
        defaults['sections'] = sections

        return defaults

    @classmethod
    def read_and_parse_file_configuration(
            cls, config_file='DAE.conf', work_dir=None, defaults=None,
            environment_override=True):
        '''
        Read and parse DAE configuration stored in a file. This method overload
        :func:`read_and_parse_file_configuration <dae.configuration.config_parser_base.ConfigParserBase.read_and_parse_file_configuration>`
        from the :class:`ConfigParserBase <dae.configuration.config_parser_base.ConfigParserBase>`
        class by adding ``environment_override`` parameter. It also combine
        default and override values from environment and from predifined in the
        class property :attr:`DEFAULT_SECTION_VALUES` above.

        :param str config_file: file which contains configuration.
        :param str work_dir: working directory which will be added as
                             ``work_dir`` and ``wd`` default values in the
                             configuration.
        :param defaults: default values which will be used when configuration
                         file is readed.
        :param bool environment_override: it shows if
                                          :func:`read_config <dae.configuration.config_parser_base.ConfigParserBase.read_config>`
                                          will use `override` from `defaults`.
        :type defaults: dict or None
        :return: read and parsed configuration.
        :rtype: Box or None
        '''
        if work_dir is None:
            work_dir = os.environ.get('DAE_DB_DIR', None)
        assert work_dir is not None
        work_dir = os.path.abspath(work_dir)
        assert os.path.exists(work_dir)
        assert os.path.isdir(work_dir)

        defaults = cls._get_defaults(environment_override, defaults)

        ois = defaults.get('override', {}).pop('impala_storage', None)

        config = super(DAEConfigParser, cls).read_file_configuration(
            config_file, work_dir, defaults=defaults
        )

        for genotype_storage_id in config.get('storage', {}).keys():
            genotype_storage = config.storage[genotype_storage_id]
            if genotype_storage.type == 'impala':
                if ois:
                    genotype_storage = \
                        recursive_dict_update(genotype_storage, ois)
            config.storage[genotype_storage_id] = genotype_storage

        config = cls.parse(config, dae_data_dir=work_dir)

        return config

    @classmethod
    def parse(cls, config, dae_data_dir=None):
        '''
        Parse all of the sections in the DAE configuration. This method
        overload :func:`parse <dae.configuration.config_parser_base.ConfigParserBase.parse>`
        from :class:`ConfigParserBase <dae.configuration.config_parser_base.ConfigParserBase>`
        class by adding ``dae_data_dir`` parameter.

        :param config: configuration.
        :param dae_data_dir: path of data directory
        :type config: Box or dict
        :type dae_data_dir: str or None
        :return: parsed configuration.
        :rtype: Box or dict or None
        '''
        config = super(DAEConfigParser, cls).parse(config)
        config = super(DAEConfigParser, cls).parse_section(config)

        assert config is not None

        for storage in config.get('storage', {}).keys():
            config.storage[storage] = \
                super(DAEConfigParser, cls).parse(config.storage[storage])

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

        if config.gpfjs.permission_denied_prompt_file:
            filepath = config.gpfjs.permission_denied_prompt_file
            assert os.path.exists(filepath), filepath
            with open(filepath, 'r') as prompt_file:
                config.gpfjs.permission_denied_prompt = prompt_file.read()

        return config
