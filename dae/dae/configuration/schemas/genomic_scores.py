from dae.configuration.gpf_config_parser import validate_existing_path

genomic_score_schema = {
    "id ": {"type": "string"},
    "file ": {
        "type": "string",
        "check_with": validate_existing_path,
        "coerce": "abspath",
    },
    "desc ": {"type": "string"},
    "bins ": {"type": "integer"},
    "yscale ": {"type": "string", "allowed": ["linear", "log"]},
    "xscale ": {"type": "string", "allowed": ["linear", "log"]},
    "help_file ": {
        "type": "string",
        "check_with": validate_existing_path,
        "coerce": "abspath",
    },
}


genomic_scores_schema = {
    "genomic_scores": {
        "type": "dict",
        "allow_unknown": True,
        "valuesrules": {"type": "dict", "schema": genomic_score_schema},
    }
}
