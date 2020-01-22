regression_schema = {
    "instrument_name": {"type": "string"},
    "measure_name": {"type": "string"},
    "jitter": {"type": "float"},
    "display_name": {"type": "string"},
}

phenotype_data_schema = {
    "name": {"type": "string"},
    "dbfile": {"type": "string", "path": "absolute"},
    "browser_dbfile": {"type": "string", "path": "absolute"},
    "browser_images_dir": {"type": "string", "path": "absolute"},
    "browser_images_url": {"type": "string", "path": "absolute"},
}

pheno_conf_schema = {
    "phenotype_data": {"type": "dict", "schema": phenotype_data_schema},
    "regression": {
        "type": "dict",
        "valuesrules": {"type": "dict", "schema": regression_schema},
    },
}
