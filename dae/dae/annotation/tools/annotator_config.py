from dae.configuration.config_parser_base import ConfigParserBase


def annotation_config_cli_options(gpf_instance):
    options = [
        ('--annotation', {
            'help': 'config file location; default is "annotation.conf" '
            'in the instance data directory $DAE_DB_DIR '
            '[default: %(default)s]',
            'default': gpf_instance.dae_config.annotation.conf_file,
            'action': 'store',
            'dest': 'annotation_config',
        }),
        ('-c', {
            'help': 'chromosome column number/name [default: %(default)s]'
        }),
        ('-p', {
            'help': 'position column number/name [default: %(default)s]'
        }),
        ('-x', {
            'help': 'location (chr:position) column number/name '
            '[default: %(default)s]'
        }),
        ('-v', {
            'help': 'variant (CSHL format) column number/name'
        }),
        ('-r', {
            'help': 'reference column number/name'
        }),
        ('-a', {
            'help': 'alternative column number/name'
        }),
        ('--vcf', {
            'help': 'if the variant description uses VCF convention '
            '[default: %(default)s]',
            'default': False,
            'action': 'store_true'
        }),
        ('--Graw', {
            'help': 'genome file location [default: %(default)s]',
            'default': gpf_instance.genomes_db.get_genome_file(),
        }),
        ('--Traw', {
            'help': 'gene model id [default: %(default)s]',
            'default': gpf_instance.genomes_db.get_gene_model_id(),
        }),
    ]

    return options


class AnnotationConfigParser(ConfigParserBase):

    SPLIT_STR_LISTS = (
        'virtual_columns',
    )

    @classmethod
    def read_and_parse_file_configuration(
            cls, options, config_file, work_dir, genomes_db, defaults=None):
        if defaults is None:
            defaults = {}
        if 'values' not in defaults:
            defaults['values'] = {}
        for key, option in options.items():
            defaults['values'][f'options.{key}'] = option

        config = super(AnnotationConfigParser, cls).read_file_configuration(
            config_file, work_dir, defaults
        )

        config.options = options

        config = cls.parse(config, genomes_db)

        return config

    @classmethod
    def parse(cls, config, genomes_db):
        config = cls._setup_defaults(config, genomes_db)

        config['columns'] = {}
        config['native_columns'] = []
        config['virtual_columns'] = []
        config['output_columns'] = []
        config['sections'] = []

        for config_section in config.values():
            if not isinstance(config_section, dict):
                continue
            if 'annotator' not in config_section:
                continue
            config_section = cls.parse_section(config_section, genomes_db)

            config['sections'].append(config_section)

        return config

    @classmethod
    def parse_section(cls, config_section, genomes_db):
        assert 'annotator' in config_section, config_section

        config_section = cls._setup_defaults(config_section, genomes_db)

        config_section = \
            super(AnnotationConfigParser, cls).parse_section(config_section)

        config_section['sections'] = []

        config_section.columns = config_section.get('columns', {})

        config_section.native_columns = list(config_section.columns.keys())
        config_section.virtual_columns = \
            config_section.get('virtual_columns', [])
        assert all([
            c in config_section.columns.values()
            for c in config_section.virtual_columns])

        config_section.output_columns = [
            c for c in config_section.columns.values()
            if c not in config_section.virtual_columns
        ]

        return config_section

    @staticmethod
    def _setup_defaults(config, genomes_db):
        if config.options.vcf:
            assert not config.options.v, [config.annotator, config.options.v]

            if config.options.c is None:
                config.options.c = 'CHROM'
            if config.options.p is None:
                config.options.p = 'POS'
            if config.options.r is None:
                config.options.r = 'REF'
            if config.options.a is None:
                config.options.a = 'ALT'
        else:
            if config.options.x is None and config.options.c is None:
                config.options.x = 'location'
            if config.options.v is None:
                config.options.v = 'variant'

        if config.options.prom_len is None:
            config.options.prom_len = 0

        config.genomes_db = genomes_db
        config.genome = genomes_db.get_genome(config.options.Graw)
        config.gene_models = genomes_db.get_gene_models(config.options.Traw)
        assert config.genomes_db is not None
        assert config.genome is not None
        assert config.gene_models is not None

        return config


class ScoreFileConfigParser(ConfigParserBase):

    SPLIT_STR_LISTS = (
        'header',
        'score',
        'str',
        'float',
        'int',
        'list(str)',
        'list(float)',
        'list(int)',
    )

    CAST_TO_BOOL = (
        'chr_prefix',
    )
