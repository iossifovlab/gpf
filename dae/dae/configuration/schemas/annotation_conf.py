from dae.configuration.gpf_config_parser import validate_path
from dae.configuration.schemas.genomic_score_database import \
    genomic_score_schema

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
            "chain_file": {
                "type": "string",
                "check_with": validate_path,
                "coerce": "abspath",
            },
            "target_genome": {
                "type": "string",
                "check_with": validate_path,
                "coerce": "abspath",
                "required": False
            },
            "scores_directory": {
                "type": "string",
                "check_with": validate_path,
                "coerce": "abspath",
            },
            "vcf": {"type": "boolean"},
            "prom_len": {"type": "integer", "default": 0},
            "direct": {"type": "boolean"},
            "region": {"type": "string", "required": False},
            "liftover": {"type": "string", "required": False},

            # "c": {"type": "string", "required": False},
            # "p": {"type": "string", "required": False},
            # "r": {"type": "string", "required": False},
            # "a": {"type": "string", "required": False},
            # "v": {"type": "string", "required": False},
            # "x": {"type": "string", "required": False},
            # "s": {"type": "string", "required": False},
        },
    },
    "columns": {
        "type": "dict",
        "default": dict(),
        "valuesrules": {"type": "string"},
    },
    "virtual_columns": {
        "type": "list",
        "default": list(),
        "schema": {"type": "string"},
    },
}

score_schema = {
    "type": "dict",
    "schema": {
        "id": {"type": "string"},
        "liftover": {"type": "string"},
        "override": {"type": "dict", "schema": genomic_score_schema}
    }
}

annotation_conf_schema = {
    "variant_effect": {"type": "string"},
    "liftover": {"type": "string"},
    "genomic_scores": {"type": "dict", "valuesrules": {"type": "string"}}
}
