from dae.configuration.schemas.person_sets import person_set_collections_schema
from dae.configuration.utils import validate_existing_path, validate_path

regression_schema = {
    "instrument_name": {"type": "string"},
    "measure_names": {"type": "list", "schema": {"type": "string"}},
    "measure_name": {"type": "string"},
    "jitter": {"type": "float", "default": 0.1},
    "display_name": {"type": "string"},
}

regression_conf_schema = {
    "regression": {
        "type": "dict",
        "valuesrules": {"type": "dict", "schema": regression_schema},
    },
}

pheno_conf_schema = {
    "id": {"type": "string", "required": True},
    "name": {"type": "string", "required": False},
    "enabled": {"type": "boolean", "default": True},
    "type": {
        "type": "string",
        "allowed": ["study", "group"],
    },
    "conf_dir": {
        "type": "string",
        "check_with": validate_existing_path,
        "coerce": "abspath",
        "required": True,
    },
    "dbfile": {
        "type": "string",
        "check_with": validate_existing_path,
        "coerce": "abspath",
        "dependencies": {
            "type": ["study"],
        },
    },
    "phenotype_storage": {
        "type": "dict",
        "schema": {
            "id": {"type": "string"},
            "db": {"type": "string"},
        },
    },
    "children": {
        "type": "list",
        "schema": {"type": "string"},
        "dependencies": {
            "type": ["group"],
        },
    },
    "browser_images_url": {"type": "string"},
    **regression_conf_schema,
    "person_set_collections": person_set_collections_schema,
    "common_report": {
        "type": "dict",
        "schema": {
            "enabled": {"type": "boolean", "required": True},
            "selected_person_set_collections": {
                "type": "dict",
                "schema": {
                    "denovo_report": {
                        "type": "list", "schema": {"type": "string"},
                    },
                    "family_report": {
                        "type": "list", "schema": {"type": "string"},
                    },
                },
                "default": {},
            },
            "draw_all_families": {"type": "boolean", "default": False},
            "file_path": {
                "type": "string",
                "check_with": validate_path,
                "coerce": "abspath",
                "default": "common_report.json",
            },
        },
        "default": {"enabled": False},
    },
}

groups_file_schema = {
    "pheno_groups": {"type": "list", "schema": {
        "type": "dict",
        "schema": {
            "pheno_id": {"type": "string"},
            "children": {"type": "list", "schema": {"type": "string"}},
        },
    }},
}
