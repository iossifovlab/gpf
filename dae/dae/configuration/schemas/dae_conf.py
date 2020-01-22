config_reference_schema = {
    "confFile": {"type": "string", "required": True, "path": True},
    "dir": {"type": "string"},
}

impala_schema = {
    "host": {"type": "string"},
    "port": {"type": "integer"},
    "db": {"type": "string"},
}


hdfs_schema = {
    "host": {"type": "string"},
    "port": {"type": "integer"},
    "base_dir": {"type": "string", "path": True},
}


storage_schema = {
    "type": {"type": "string", "allowed": ["impala", "filesystem"]},
    "dir": {"type": "string", "path": True},
    "impala": {
        "type": "dict",
        "dependencies": {"type": "impala"},
        "schema": impala_schema,
    },
    "hdfs": {
        "type": "dict",
        "dependencies": {"type": "impala"},
        "schema": hdfs_schema,
    },
}


dae_conf_schema = {
    "instance_id": {"type": "string"},
    "genotype_storage": {
        "type": "dict",
        "schema": {"default": {"type": "string"}},
    },
    "storage": {"type": "dict", "schema": storage_schema},
    "studiesDB": {"type": "dict", "schema": config_reference_schema},
    "datasetsDB": {"type": "dict", "schema": config_reference_schema},
    "genomesDB": {"type": "dict", "schema": config_reference_schema},
    "genomicScoresDB": {"type": "dict", "schema": config_reference_schema},
    "annotation": {"type": "dict", "schema": config_reference_schema},
    "phenotypeData": {"type": "dict", "schema": {"dir": {"type": "string"}}},
    "geneInfoDB": {"type": "dict", "schema": config_reference_schema},
    "defaultStudyConfig": {"type": "dict", "schema": config_reference_schema},
    "gpfjs": {
        "type": "dict",
        "schema": {
            "permissionDeniedPromptFile": {"type": "string", "path": True}
        },
    },
}
