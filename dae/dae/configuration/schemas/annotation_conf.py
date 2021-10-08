from dae.configuration.schemas.genomic_resources_database import \
    default_annotation_schema

annotator_schema = {
    "type": "dict",
    "schema": {
        "annotator": {"type": "string", "required": True},
        "resource": {"type": "string"},
        "gene_models": {"type": "string"},
        "chain": {"type": "string"},
        "target_genome": {"type": "string"},
        "liftover": {"type": "string"},
        "override": {"type": "dict", "schema": default_annotation_schema}
    }
}

annotation_conf_schema = {
    "effect_annotators": {
        "type": "list",
        "schema": annotator_schema,
    },
    "liftover_annotators": {
        "type": "list", 
        "schema": annotator_schema,
    },
    "score_annotators": {
        "type": "list",
        "schema": annotator_schema,
    }
}
