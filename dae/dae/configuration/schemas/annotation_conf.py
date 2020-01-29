from dae.configuration.gpf_config_parser import validate_path

# TODO Add additional rules for specific option fields

annotation_section_schema = {
    "annotator": {"type": "string"},
    "options": {
        "type": "dict",
        "default": dict(),
        "schema": {
            "mode": {"type": "string"},
            "scores_file": {
                "type": "string",
                "check_with": validate_path,
                "coerce": "abspath",
            },
            "vcf": {"type": "boolean", "default": False},
            "prom_len": {"type": "integer", "default": 0},
            "c": {"type": "string", "required": False},
            "p": {"type": "string", "required": False},
            "r": {"type": "string", "required": False},
            "a": {"type": "string", "required": False},
            "v": {"type": "string", "required": False},
            "x": {"type": "string", "required": False},
        },
    },
    "columns": {"type": "dict", "default": dict(), "valuesrules": {"type": "string"}},
    "virtual_columns": {"type": "list", "default": list(), "schema": {"type": "string"}},
}

annotation_conf_schema = {
    "sections": {
        "type": "list",
        "schema": {
            "type": "dict",
            "schema": annotation_section_schema
        }
    }
}
