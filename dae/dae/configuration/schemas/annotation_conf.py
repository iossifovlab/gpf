from dae.configuration.schemas.genomic_score_database import \
    genomic_score_schema

annotator_schema = {
    "type": "dict",
    "schema": {
        "annotator": {"type": "string", "required": True},
        "resource": {"type": "string"},
        "genome": {"type": "string"},
        "gene_models": {"type": "string"},
        "liftover": {"type": "string"},
        "override": {"type": "dict", "schema": genomic_score_schema}
    }
}

annotation_conf_schema = {
    "annotators": {"type": "list", "schema": annotator_schema}
}
