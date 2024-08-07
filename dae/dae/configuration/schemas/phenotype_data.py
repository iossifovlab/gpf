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

phenotype_data_schema = {
    "enabled": {"type": "boolean", "default": True},
    "name": {"type": "string"},
    "dbfile": {
        "type": "string",
        "check_with": validate_existing_path,
        "coerce": "abspath",
    },
    "browser_images_url": {"type": "string"},
}

pheno_conf_schema = {
    "conf_dir": {
        "type": "string",
        "check_with": validate_existing_path,
        "coerce": "abspath",
        "required": True,
    },
    "phenotype_data": {"type": "dict", "schema": phenotype_data_schema},
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
