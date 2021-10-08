
attr_schema = {
    "type": "dict",
    "schema": {
        "name": {"type": "string"},
        "index": {"type": "integer"},
    }
}

prefix_schema = {
    "add_prefix": {"type": "string"},
    "del_prefix": {"type": "string"},
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
                },
                "histogram": {
                    "type": "dict",
                    "schema": {
                        "bins_count": {"type": "integer"},
                        "x_min": {"type": "float"},
                        "x_max": {"type": "float"},
                        "x_scale": {
                            "type": "string",
                            "allowed": ["linear", "log"]
                        },
                        "y_scale": {
                            "type": "string",
                            "allowed": ["linear", "log"]
                        },
                        "x_min_log": {
                            "type": "float",
                            "dependencies": {"x_scale": "log"}
                        }
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
    "chrom_prefix": {"type": "dict", "schema": {
        "variant_coordinates": {"type": "dict", "schema": prefix_schema},
        "target_coordinates": {"type": "dict", "schema": prefix_schema},
    }},
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

    "PARS": {
        "type": "dict",
        "valuesrules": {"type": "list", "schema": {"type": "string"}},
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
