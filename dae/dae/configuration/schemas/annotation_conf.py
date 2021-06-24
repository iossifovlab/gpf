from dae.configuration.schemas.genomic_score_database import \
    genomic_score_schema

resource_schema = {
    "type": "dict",
    "schema": {
        "id": {"type": "string", "required": True},
        "type": {
            "type": "string",
            "allowed": ["genomic_score", "liftover", "variant_effect"],
            "required": True
        },
        "liftover": {"type": "string"},
        "override": {"type": "dict", "schema": genomic_score_schema}
    }
}

annotation_conf_schema = {
    "resources": {"type": "list", "schema": resource_schema}
}
