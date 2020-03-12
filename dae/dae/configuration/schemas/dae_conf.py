from dae.configuration.gpf_config_parser import (
    validate_existing_path,
    validate_path,
)

config_reference_schema = {
    "conf_file": {
        "type": "string",
        "required": True,
        "check_with": validate_existing_path,
        "coerce": "abspath",
    },
    "dir": {
        "type": "string",
        "check_with": validate_existing_path,
        "coerce": "abspath",
    },
}

impala_schema = {
    "host": {"type": "string"},
    "port": {"type": "integer"},
    "db": {"type": "string"},
}


hdfs_schema = {
    "host": {"type": "string"},
    "port": {"type": "integer"},
    "base_dir": {"type": "string", "check_with": validate_path},
}


storage_schema = {
    "storage_type": {"type": "string", "allowed": ["impala", "filesystem"]},
    "dir": {
        "type": "string",
        "check_with": validate_path,
        "coerce": "abspath",
    },
    "impala": {
        "type": "dict",
        "dependencies": {"storage_type": "impala"},
        "schema": impala_schema,
    },
    "hdfs": {
        "type": "dict",
        "dependencies": {"storage_type": "impala"},
        "schema": hdfs_schema,
    },
}


dae_conf_schema = {
    "dae_data_dir": {
        "type": "string",
        "check_with": validate_existing_path,
        "coerce": "abspath",
    },
    "annotation_defaults": {
        "type": "dict",
        "schema": {"wd": {"type": "string"}, "data_dir": {"type": "string"}},
    },
    # FIXME This is only used for the default genotype storage param
    # It should be a key in the root section
    "genotype_storage": {
        "type": "dict",
        "schema": {"default": {"type": "string"}},
    },
    "storage": {
        "type": "dict",
        "valuesrules": {"type": "dict", "schema": storage_schema},
    },
    "studies_db": {"type": "dict", "schema": config_reference_schema},
    "datasets_db": {"type": "dict", "schema": config_reference_schema},
    "genomes_db": {"type": "dict", "schema": config_reference_schema},
    "genomic_scores_db": {"type": "dict", "schema": config_reference_schema},
    "annotation": {"type": "dict", "schema": config_reference_schema},
    "phenotype_data": {
        "type": "dict",
        "schema": {
            "dir": {
                "type": "string",
                "check_with": validate_existing_path,
                "coerce": "abspath",
            }
        },
    },
    "gene_info_db": {"type": "dict", "schema": config_reference_schema},
    "default_study_config": {
        "type": "dict",
        "schema": config_reference_schema,
    },
    "gpfjs": {
        "type": "dict",
        "schema": {
            "permission_denied_prompt_file": {
                "type": "string",
                "check_with": validate_existing_path,
                "coerce": "abspath",
            }
        },
    },
    "enrichment": {"type": "dict", "schema": config_reference_schema},
}
