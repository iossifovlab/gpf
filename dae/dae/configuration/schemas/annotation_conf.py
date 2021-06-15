from dae.configuration.gpf_config_parser import validate_path
from dae.configuration.schemas.genomic_score_database import \
    genomic_score_schema

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
    "genomic_scores": {"type": "list", "schema": score_schema},
}
