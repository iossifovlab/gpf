from dae.configuration.gpf_config_parser import GPFConfigParser
from dae.configuration.schemas.annotation_conf import annotation_conf_schema
from dae.utils.dict_utils import recursive_dict_update

from box import Box


def annotation_config_cli_options(gpf_instance):
    options = [
        (
            "--annotation",
            {
                "help": 'config file location; default is "annotation.conf" '
                "in the instance data directory $DAE_DB_DIR "
                "[default: %(default)s]",
                "default": gpf_instance.dae_config.annotation.conf_file,
                "action": "store",
                "dest": "annotation_config",
            },
        ),
        (
            "-c",
            {"help": "chromosome column number/name [default: %(default)s]"},
        ),
        ("-p", {"help": "position column number/name [default: %(default)s]"}),
        (
            "-x",
            {
                "help": "location (chr:position) column number/name "
                "[default: %(default)s]"
            },
        ),
        ("-v", {"help": "variant (CSHL format) column number/name"}),
        ("-r", {"help": "reference column number/name"}),
        ("-a", {"help": "alternative column number/name"}),
        (
            "--vcf",
            {
                "help": "if the variant description uses VCF convention "
                "[default: %(default)s]",
                "default": False,
                "action": "store_true",
            },
        ),
        # fmt: off
        (
            "--Graw",
            {
                "help": "genome file location [default: %(default)s]",
                "default":
                gpf_instance.genomes_db.get_genomic_sequence_filename(),
            },
        ),
        (
            "--Traw",
            {
                "help": "gene model id [default: %(default)s]",
                "default":
                gpf_instance.genomes_db.get_default_gene_models_id(),
            },
        ),
        # fmt: on
    ]

    return options


class AnnotationConfigParser:
    @classmethod
    def read_and_parse_file_configuration(cls, options, config_file):

        config = GPFConfigParser.load_config(
            config_file, annotation_conf_schema
        ).to_dict()

        config["options"] = options
        config["columns"] = {}
        config["native_columns"] = []
        config["virtual_columns"] = []
        config["output_columns"] = []

        config = Box(
            config,
            default_box=True,
            default_box_attr=None
        )
        print(config.options)

        config = cls._setup_defaults(config)

        parsed_sections = list()
        for config_section in config.sections:
            if config_section.annotator is None:
                continue
            config_section_dict = recursive_dict_update(
                {"options": options}, config_section.to_dict()
            )
            parsed_sections.append(cls.parse_section(config_section_dict))

        config["sections"] = parsed_sections

        return Box(
            config,
            frozen_box=True,
            default_box=True,
            default_box_attr=None
        )

    @classmethod
    def parse_section(cls, config_section):

        config_section = Box(
            config_section,
            default_box=True,
            default_box_attr=None
        )

        config_section = cls._setup_defaults(config_section)

        config_section["sections"] = list()
        config_section["native_columns"] = list(config_section.columns.keys())

        assert all([
            c in config_section["columns"]
            for c in config_section["virtual_columns"]
        ])

        config_section["output_columns"] = list(
            set(config_section["columns"])
            - set(config_section["virtual_columns"])
        )

        return config_section

    @staticmethod
    def _setup_defaults(config):
        if config.options.vcf:
            assert not config.options.v, [config.annotator, config.options.v]

            if config.options.c is None:
                config.options.c = "CHROM"
            if config.options.p is None:
                config.options.p = "POS"
            if config.options.r is None:
                config.options.r = "REF"
            if config.options.a is None:
                config.options.a = "ALT"
        else:
            if config.options.x is None and config.options.c is None:
                config.options.x = "location"
            if config.options.v is None:
                config.options.v = "variant"

        return config
