from dae.configuration.gpf_config_parser import validate_existing_path

attr_schema = {
    "type": "dict",
    "schema": {
        "name": {"type": "string"},
        "index": {"type": "integer"},
    }
}

target_genome_schema = {
    "filename": {"type": "string"},
    "del_chrom_prefix": {"type": "string"},
}

default_annotation_schema = {
    "attributes": {
        "type": "list",
        "schema": {
            "type": "dict",
            "schema": {
                "source": {"type": "string"},
                "dest": {"type": "string"},
                "aggregator": {
                    "type": "dict", "schema": {
                        "position": {"type": "string"},
                        "nucleotide": {"type": "string"}
                    }
                }
            }
        }
    }
}

genomic_score_schema = {
    "id": {"type": "string"},
    "name": {"type": "string"},
    "resource_type": {"type": "string", "required": True},
    "filename": {
        "type": "string",
        "required": True,
        "coerce": "abspath",
    },
    "format": {"type": "string"},
    "has_header": {"type": "boolean"},
    "add_chrom_prefix": {"type": "string"},
    "index_file": {
        "type": "dict",
        "schema": {
            "filename": {
                "type": "string",
                "required": True,
                "coerce": "abspath",
            },
            "format": {"type": "string"},
        },
    },
    "version": {
        "type": "dict",
        "schema": {
            "score_version": {"type": "string"}
        },
    },
    "target_genome": {
        "type": "dict",
        "schema": target_genome_schema,
    },
    "type_aggregators": {
        "type": "list", "schema": {
            "type": "dict", "schema": {
                "type": {"type": "string"},
                "aggregator": {"type": "string"}
            }
        }
    },
    "scores": {
        "type": "list",
        "schema": {
            "type": "dict",
            "schema": {
                "id": {"type": "string"},
                "name": {"type": "string"},
                "type": {"type": "string"},
                "desc": {"type": "string"},
                "index": {"type": "integer"},
            }
        }
    },
    "default_annotation": {
        "type": "dict",
        "schema": default_annotation_schema,
    },
    "meta": {"type": "string"},
}

genomic_sequence_schema = {
    "id": {"type": "string"},
    "name": {"type": "string"},
    "resource_type": {"type": "string", "required": True},
    "filename": {
        "type": "string",
        "required": True,
        "coerce": "abspath",
    },
    "format": {"type": "string"},
    "chrom_prefix": {"type": "string"},

    "index_file": {
        "type": "dict",
        "schema": {
            "filename": {
                "type": "string",
                "required": True,
                "coerce": "abspath",
            },
            "format": {"type": "string"},
        },
    },

    "meta": {"type": "string"},
}


gene_models_schema = {
    "id": {"type": "string"},
    "name": {"type": "string"},
    "resource_type": {"type": "string", "required": True},
    "filename": {
        "type": "string",
        "required": True,
        "coerce": "abspath",
    },
    "format": {"type": "string"},

    "meta": {"type": "string"},
}
