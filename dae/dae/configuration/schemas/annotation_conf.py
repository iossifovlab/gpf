from dae.configuration.schemas.genomic_resources_database import \
    default_annotation_schema

annotator_schema = {
    "type": "dict",
    "schema": {
        "annotator": {"type": "string", "required": True},
        "resource": {"type": "string"},
        "genome": {"type": "string"},
        "gene_models": {"type": "string"},
        "liftover": {"type": "string"},
        "override": {"type": "dict", "schema": default_annotation_schema}
    }
}

annotation_conf_schema = {
    "annotators": {"type": "list", "schema": annotator_schema}
}
