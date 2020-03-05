from dae.configuration.gpf_config_parser import GPFConfigParser
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
        (
            "--Graw",
            {
                "help": "genome file location [default: %(default)s]",
                "default": gpf_instance.genomes_db.get_genome_file(),
            },
        ),
        (
            "--Traw",
            {
                "help": "gene model id [default: %(default)s]",
                "default": gpf_instance.genomes_db.get_gene_model_id(),
            },
        ),
    ]

    return options


class AnnotationConfigParser:
    @classmethod
    def read_and_parse_file_configuration(
        cls, options, config_file, defaults=None
    ):

        if defaults is None:
            defaults = {}
        if "values" not in defaults:
            defaults["values"] = {}
        if "options" not in defaults:
            defaults["values"]["options"] = {}

        defaults["values"]["options"].update(options)

        defaults_dict = defaults["values"]

        config = GPFConfigParser.load_config(
            config_file, annotation_conf_schema
        )

        config = GPFConfigParser.modify_tuple(config, defaults_dict)
        config = GPFConfigParser.modify_tuple(config, {"options": options})
        config = cls._setup_defaults(config)

        config = GPFConfigParser.modify_tuple(config, {"columns": {}})
        config = GPFConfigParser.modify_tuple(config, {"native_columns": []})
        config = GPFConfigParser.modify_tuple(config, {"virtual_columns": []})
        config = GPFConfigParser.modify_tuple(config, {"output_columns": []})

        parsed_sections = list()
        for config_section in config.sections:
            if config_section.annotator is None:
                continue
            config_dict = GPFConfigParser._namedtuple_to_dict(config_section)
            config_dict = recursive_dict_update(config_dict, defaults_dict)
            config_section = GPFConfigParser._dict_to_namedtuple(config_dict)
            config_section = cls.parse_section(config_section)
            parsed_sections.append(config_section)
        config = GPFConfigParser.modify_tuple(
            config, {"sections": parsed_sections}
        )
        return config

    @classmethod
    def parse_section(cls, config_section):
        config_section = cls._setup_defaults(config_section)

        config_section = GPFConfigParser.modify_tuple(
            config_section, {"sections": []}
        )

        native_columns = list(config_section.columns._fields)
        config_section = GPFConfigParser.modify_tuple(
            config_section, {"native_columns": native_columns}
        )
        assert all(
            [
                c in config_section.columns
                for c in config_section.virtual_columns
            ]
        )

        output_columns = [
            c
            for c in config_section.columns
            if c not in config_section.virtual_columns
        ]
        config_section = GPFConfigParser.modify_tuple(
            config_section, {"output_columns": output_columns}
        )

        return config_section

    @staticmethod
    def _setup_defaults(config):
        def modify_config_options(config, new_vals):
            config_opts = config.options
            config_opts = GPFConfigParser.modify_tuple(config_opts, new_vals)
            return GPFConfigParser.modify_tuple(
                config, {"options": config_opts}
            )

        if config.options.vcf:
            assert not config.options.v, [config.annotator, config.options.v]

            if config.options.c is None:
                config = modify_config_options(config, {"c": "CHROM"})
            if config.options.p is None:
                config = modify_config_options(config, {"p": "POS"})
            if config.options.r is None:
                config = modify_config_options(config, {"r": "REF"})
            if config.options.a is None:
                config = modify_config_options(config, {"a": "ALT"})
        else:
            if config.options.x is None and config.options.c is None:
                config = modify_config_options(config, {"x": "location"})
            if config.options.v is None:
                config = modify_config_options(config, {"v": "variant"})

        return config
