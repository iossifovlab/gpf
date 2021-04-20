from dae.configuration.gpf_config_parser import (
    validate_existing_path,
    validate_path,
)

gene_set_schema = {
    "type": "dict",
    "schema": {
        "collection_id": {"type": "string", "default": "main"},
        "set_id": {"type": "string"}
    }
}

genomic_score_schema = {
    "type": "dict",
    "schema": {
        "score_name": {"type": "string"},
        "format": {"type": "string", "default": "%s"}
    }
}

autism_gene_tool_config = {
    "gene_sets": {
        "type": "list",
        "required": True,
        "schema": {
            "type": "dict",
            "schema": {
                "category": {"type": "string"},
                "display_name": {"type": "string"},
                "sets": {"type": "list", "schema": gene_set_schema}
            },
        }
    },
    "genomic_scores": {
        "type": "list",
        "required": True,
        "schema": {
            "type": "dict",
            "schema": {
                "category": {"type": "string"},
                "display_name": {"type": "string"},
                "scores": {"type": "list", "schema": genomic_score_schema}
            },
        }
    },
    "datasets": {
        "required": True,
        "type": "dict",
        "valuesrules": {
            "type": "dict", "schema": {
                "person_sets": {"type": "list", "schema": {
                        "type": "dict",
                        "schema": {
                            "set_name": {"type": "string"},
                            "collection_name": {"type": "string"},
                        }
                    }
                },
                "effects": {"type": "list", "schema": {"type": "string"}}
            }
        }
    },
    "default_dataset": {"type": "string", "required": True}
}
