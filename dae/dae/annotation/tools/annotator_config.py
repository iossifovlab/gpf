from box import Box
from ast import literal_eval
from collections import OrderedDict

from dae.DAE import genomesDB

from dae.configuration.dae_config_parser import DAEConfigParser


def annotation_config_cli_options(dae_config):
    options = [
        ('--annotation', {
            'help': 'config file location; default is "annotation.conf" '
            'in the instance data directory $DAE_DB_DIR '
            '[default: %(default)s]',
            'default': dae_config.annotation.conf_file,
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
            'default': genomesDB.get_genome_file(),
        }),
    ]

    return options


class AnnotationConfigParser(DAEConfigParser):

    @classmethod
    def read_and_parse_file_configuration(
            cls, options, config_file, work_dir, defaults=None):
        config = super(AnnotationConfigParser, cls).read_file_configuration(
            config_file, work_dir, defaults
        )

        config = cls.parse(
            config,
            name="pipeline",
            annotator_name="annotation_pipeline.Pipeline",
            options=options,
            columns_config=OrderedDict(),
            virtuals=[]
        )

        return config

    @classmethod
    def parse(
            cls, config, name, annotator_name, options, columns_config,
            virtuals, parse_sections=True):
        config.name = name
        config.annotator_name = annotator_name
        config.options = options
        config.columns_config = columns_config

        config.native_columns = list(columns_config.keys())
        config.virtual_columns = list(virtuals)
        assert all([
            c in config.columns_config.values()
            for c in config.virtual_columns])

        config.output_columns = [
            c for c in config.columns_config.values()
            if c not in config.virtual_columns
        ]

        config.pipeline_sections = []

        config = cls._setup_defaults(config)

        if parse_sections:
            for section_name, config_section in config.items():
                if not isinstance(config_section, dict):
                    continue
                if 'annotator' not in config_section:
                    continue

                config_section = cls.parse_section(
                    section_name, config_section, options)
                config.pipeline_sections.append(config_section)

        return config

    @classmethod
    def parse_section(cls, section_name, config_section, options):
        assert 'annotator' in config_section, [section_name, config_section]

        annotator_name = config_section['annotator']
        options = dict(options.to_dict())
        if 'options' in config_section:
            for key, val in config_section['options'].items():
                try:
                    val = literal_eval(val)
                except Exception:
                    pass
                options[key] = val

        options = Box(options, default_box=True, default_box_attr=None)

        if 'columns' in config_section:
            columns_config = OrderedDict(config_section['columns'])
        else:
            columns_config = OrderedDict()

        if 'virtuals' not in config_section:
            virtuals = []
        else:
            virtuals = [
                c.strip() for c in config_section['virtuals'].split(',')
            ]
        config_section = cls.parse(
            config_section,
            name=section_name,
            annotator_name=annotator_name,
            options=options,
            columns_config=columns_config,
            virtuals=virtuals,
            parse_sections=False
        )

        return config_section

    @staticmethod
    def _setup_defaults(config):
        if config.options.vcf:
            assert not config.options.v, \
                [config.name, config.annotator_name, config.options.v]

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
        if config.options.Graw is None:
            config.genome_file = genomesDB.get_genome_file()
        else:
            config.genome_file = config.options.Graw
        assert config.genome_file is not None

        return config


class ScoreConfigParser(DAEConfigParser):

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
