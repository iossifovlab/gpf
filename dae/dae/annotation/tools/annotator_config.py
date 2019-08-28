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


class VariantAnnotatorConfig(object):

    def __init__(
            self, name, annotator_name, options,
            columns_config, virtuals):
        self.name = name
        self.annotator_name = annotator_name
        self.options = options
        self.columns_config = columns_config

        self.native_columns = list(columns_config.keys())
        self.virtual_columns = list(virtuals)
        assert all([
            c in self.columns_config.values()
            for c in self.virtual_columns])

        self.output_columns = [
            c for c in self.columns_config.values()
            if c not in self.virtual_columns
        ]

        self._setup_defaults()

        self.pipeline_sections = []

    def _setup_defaults(self):
        if self.options.vcf:
            assert not self.options.v, \
                [self.name, self.annotator_name, self.options.v]

            if self.options.c is None:
                self.options.c = 'CHROM'
            if self.options.p is None:
                self.options.p = 'POS'
            if self.options.r is None:
                self.options.r = 'REF'
            if self.options.a is None:
                self.options.a = 'ALT'
        else:
            if self.options.x is None and self.options.c is None:
                self.options.x = 'location'
            if self.options.v is None:
                self.options.v = 'variant'
        if self.options.Graw is None:
            self.genome_file = genomesDB.get_genome_file()
        else:
            self.genome_file = self.options.Graw
        assert self.genome_file is not None

    @staticmethod
    def build(options, config_file, work_dir, defaults=None):
        configuration = PipelineConfigParser.read_and_parse_file_configuration(
            config_file, work_dir, defaults
        )

        result = VariantAnnotatorConfig(
            name="pipeline",
            annotator_name="annotation_pipeline.Pipeline",
            options=options,
            columns_config=OrderedDict(),
            virtuals=[]
        )
        result.pipeline_sections = []

        for section_name, section_config in configuration.items():
            section_config = result._parse_config_section(
                section_name, section_config, options)
            result.pipeline_sections.append(section_config)
        return result

    @staticmethod
    def _parse_config_section(section_name, section, options):
        # section = Box(section, default_box=True, default_box_attr=None)
        assert 'annotator' in section, [section_name, section]

        annotator_name = section['annotator']
        options = dict(options.to_dict())
        if 'options' in section:
            for key, val in section['options'].items():
                try:
                    val = literal_eval(val)
                except Exception:
                    pass
                options[key] = val

        options = Box(options, default_box=True, default_box_attr=None)

        if 'columns' in section:
            columns_config = OrderedDict(section['columns'])
        else:
            columns_config = OrderedDict()

        if 'virtuals' not in section:
            virtuals = []
        else:
            virtuals = [
                c.strip() for c in section['virtuals'].split(',')
            ]
        return VariantAnnotatorConfig(
            name=section_name,
            annotator_name=annotator_name,
            options=options,
            columns_config=columns_config,
            virtuals=virtuals
        )


class PipelineConfigParser(DAEConfigParser):

    @classmethod
    def parse(cls, config):
        config.pop('config_file')

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
