from dae.configuration.utils import validate_existing_path

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
    "name": {"type": "string", "required": True},
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
    "children": {
        "type": "list",
        "schema": {"type": "string"},
        "dependencies": {
            "type": ["group"],
        },
    },
    "browser_images_url": {"type": "string"},
    **regression_conf_schema,
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
