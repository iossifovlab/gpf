attr_schema = {
    "type": "dict",
    "schema": {
        "name": {"type": "string"},
        "index": {"type": "integer"},
    }
}

attributes = {
    "chrom": attr_schema,
    "pos_begin": attr_schema,
    "pos_end": attr_schema,
    "position": attr_schema,
    "reference": attr_schema,
    "alternative": attr_schema,
    "variant": attr_schema,
    "location": attr_schema,
}

target_genome_schema = {
    "filename": {"type": "string"},
    "del_chrom_prefix": {"type": "string"},
}

genomic_score_schema = {
    "id": {"type": "string"},
    "name": {"type": "string"},
    "score_type": {"type": "string"},
    "filename": {"type": "string"},
    "format": {"type": "string"},
    "has_header": {"type": "boolean"},
    "add_chrom_prefix": {"type": "string"},
    "index_file": {
        "type": "dict",
        "schema": {
            "filename": {"type": "string"},
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
    **attributes,
    "scores": {
        "type": "list",
        "schema": {
            "type": "dict",
            "schema": {
                "id": {"type": "string"},
                "type": {"type": "string"},
                "desc": {"type": "string"},
                "index": {"type": "integer"},
            }
        }
    },
    "default_annotation": {
        "type": "dict",
        "schema": {
            "attributes": {
                "type": "list",
                "schema": {
                    "type": "dict",
                    "schema": {
                        "source": {"type": "string"},
                        "dest": {"type": "string"},
                    }
                }
            },
        }
    },
    "meta": {"type": "string"},
}
