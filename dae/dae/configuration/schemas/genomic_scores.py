from dae.configuration.gpf_config_parser import validate_existing_path

genomic_score_schema = {
    "id": {"type": "string", "required": True},
    "file": {
        "type": "string",
        "check_with": validate_existing_path,
        "coerce": "abspath",
    },
    "desc": {"type": "string"},
    "bins": {"type": "integer"},
    "yscale": {"type": "string", "allowed": ["linear", "log"]},
    "xscale": {"type": "string", "allowed": ["linear", "log"]},
    "range": {
        "type": "dict",
        "schema": {
            "start": {"type": "float"},
            "end": {"type": "float"}
        }
    },
    "help_file": {
        "type": "string",
        "check_with": validate_existing_path,
        "coerce": "abspath",
    },
}


genomic_scores_schema = {
    "scores": {"type": "list", "schema": {"type": "string"}},
    "genomic_scores": {
        "type": "dict",
        "valuesrules": {"type": "dict", "schema": genomic_score_schema},
    }
}
