from dae.configuration.gpf_config_parser import validate_existing_path

score_file_conf_schema = {
    "conf_dir": {
        "type": "string",
        "check_with": validate_existing_path,
        "coerce": "abspath",
        "required": True,
    },
    "general": {
        "type": "dict",
        "schema": {
            "header": {"type": "list", "schema": {"type": "string"}},
            "score": {"type": "list", "schema": {"type": "string"}},
            "no_score_value": {"type": "string"},
            "chr_prefix": {"type": "boolean"},
        },
    },
    "columns": {
        "type": "dict",
        "schema": {
            "chr": {"type": "string"},
            "pos_begin": {"type": "string"},
            "pos_end": {"type": "string"},
            "ref": {"type": "string"},
            "alt": {"type": "string"},
            "variant": {"type": "string"},
            "score": {"type": "list", "schema": {"type": "string"}},
        },
    },
    "score_schema": {
        "type": "dict",
        "schema": {
            "str": {"type": "list", "schema": {"type": "string"}},
            "float": {"type": "list", "schema": {"type": "string"}},
            "int": {"type": "list", "schema": {"type": "string"}},
            "list(str)": {"type": "list", "schema": {"type": "string"}},
            "list(float)": {"type": "list", "schema": {"type": "string"}},
            "list(int)": {"type": "list", "schema": {"type": "string"}},
        },
    },
    "misc": {
        "type": "dict",
        "schema": {
            "chr_prefix": {"type": "boolean"},
            "pos_base": {"type": "integer"},
            "format": {"type": "string"},
            "compression": {"type": "string"},
            "no_header": {"type": "boolean"},
            "tabix": {"type": "string"},
        },
    },
}
