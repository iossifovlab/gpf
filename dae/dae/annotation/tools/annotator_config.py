from dae.configuration.gpf_config_parser import GPFConfigParser, DefaultBox, \
    FrozenBox
from dae.configuration.schemas.annotation_conf import annotation_conf_schema
from dae.utils.dict_utils import recursive_dict_update


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
                "help": "gene model filename [default: %(default)s]",
                "default":
                gpf_instance.genomes_db.get_default_gene_models_filename(),
            },
        ),
        (
            "--TrawFormat",
            {
                "help": "gene model file format [default: %(default)s]",
                "default": "default",
            },
        ),
        # fmt: on
    ]

    return options


class AnnotationConfigParser:
    @classmethod
    def read_and_parse_file_configuration(cls, config_file):

        config = GPFConfigParser.load_config(
            config_file, annotation_conf_schema
        ).to_dict()

        config["columns"] = {}
        config["native_columns"] = []
        config["virtual_columns"] = []
        config["output_columns"] = []

        return FrozenBox(config)

    @classmethod
    def parse_section(cls, config_section):

        config_section = DefaultBox(config_section)

        config_section["sections"] = list()
        config_section["native_columns"] = list(config_section.columns.keys())

        assert all([
            c in config_section.columns.values()
            for c in config_section.virtual_columns
        ])

        config_section["output_columns"] = [
            config_section.columns[col] for col in config_section.columns
            if config_section.columns[col]
            not in config_section.virtual_columns
        ]

        return config_section
