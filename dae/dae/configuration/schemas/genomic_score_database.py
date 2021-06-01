file_schema = {
    "type": "dict",
    "schema": {
        "filename": {"type": "string"},
        "format": {"type": "string"},
        "sha256": {"type": "string"},
    }
}

identification_schema = {
    "type": "dict",
    "schema": {
        "id": {"type": "string"},
        "type": {"type": "string"},
        "desc": {"type": "string"},
        "index": {"type": "integer"},
    }
}

genomic_score = {
    "id": {"type": "string"},
    "version": {
        "type": "dict",
        "schema": {
            "score_version": {"type": "string"}
        },
    },
    "score_file": file_schema,
    "index_file": file_schema,
    "common": {
        "type": "dict",
        "schema": {
            "has_header": {"type": "boolean"},
            "add_chrom_prefix": {"type": "string"},
        }
    },
    "identification": {
        "type": "list",
        "schema": {
            "type": "dict",
            "schema": file_schema,
        }
    },
    "scores": {
        "type": "list",
        "schema": {
            "type": "dict",
            "schema": file_schema,
        }
    },
    "default_annotation": {
        "type": "dict",
        "schema": {
            "annotator": {"type": "string"},
            "attributes": {
                "type": "dict",
                "schema": {
                    "source": {"type": "string"},
                    "dest": {"type": "string"},
                }
            },
        }
    },
    "meta": {"type": "string"},
}
