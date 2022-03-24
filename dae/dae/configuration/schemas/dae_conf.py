from dae.configuration.gpf_config_parser import (
    validate_existing_path,
    validate_path,
)

config_reference_schema = {
    "conf_file": {
        "type": "string",
        "required": False,
        # "check_with": validate_existing_path,
        "coerce": "abspath",
    },
    "dir": {
        "type": "string",
        # "check_with": validate_existing_path,
        "coerce": "abspath",
    },
}

resource_schema = {
    "resource_id": {
        "type": "string",
    },
}

impala_schema = {
    "hosts": {
        "type": "list",
        "schema": {"type": "string"},
    },
    "port": {"type": "integer"},
    "db": {"type": "string"},
    "pool_size": {"type": "integer", "default": 1}
}


hdfs_schema = {
    "host": {"type": "string"},
    "port": {"type": "integer"},
    "replication": {"type": "integer", "default": 1},
    "base_dir": {"type": "string", "check_with": validate_path},
}

rsync_schema = {
    "location": {"type": "string"},
    "remote_shell": {"type": "string", "default": None, 'nullable': True},
}

remote_schema = {
    "id": {"type": "string"},
    "host": {"type": "string"},
    "gpf_prefix": {"type": "string"},
    "base_url": {"type": "string"},
    "port": {"type": "integer", "default": "8000"},
    "user": {"type": "string"},
    "password": {"type": "string"},
}

repository_schema = {
    "id": {"type": "string", },
    "type": {"type": "string", },
    "url": {"type": "string", },
    "directory": {
        "type": "string",
        "required": False,
        "coerce": "abspath",
    },
    "cache_dir": {
        "type": "string",
        "check_with": validate_path,
        "coerce": "abspath",
    },
}
grr_schema = {
    **repository_schema,
    "children": {"type": "list", "schema": {
        "type": "dict",
        "schema": repository_schema
    }}

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
    "rsync": {
        "type": "dict",
        "schema": rsync_schema,
        "dependencies": {"storage_type": "impala"},
    }
}

gene_scores_db_schema = {
    "gene_scores": {"type": "list", "schema": {"type": "string"}}
}

gene_sets_db_schema = {
    "gene_set_collections": {"type": "list", "schema": {"type": "string"}}
}

dae_conf_schema = {
    "dae_data_dir": {
        "type": "string",
        "check_with": validate_existing_path,
        "coerce": "abspath",
    },
    "conf_dir": {
        "type": "string",
        "check_with": validate_existing_path,
        "coerce": "abspath",
        "required": True,
    },

    "mirror_of": {
        "type": "string",
        "default": None, 'nullable': True,
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
        "default": {"default": "genotype_filesystem"},
    },
    "storage": {
        "type": "dict",
        "valuesrules": {"type": "dict", "schema": storage_schema},
    },
    "studies": {
        "type": "dict",
        "schema": config_reference_schema,
        "default": {"dir": "studies"},
    },
    "datasets": {
        "type": "dict",
        "schema": config_reference_schema,
        "default": {"dir": "datasets"}
    },
    "genomic_scores_db": {"type": "dict", "schema": config_reference_schema},
    "autism_gene_tool_config": {
        "type": "dict", "schema": config_reference_schema
    },
    "annotation": {"type": "dict", "schema": config_reference_schema},
    "phenotype_data": {
        "type": "dict",
        "schema": {
            "dir": {
                "type": "string",
                # "check_with": validate_existing_path,
                "coerce": "abspath",
            }
        },
    },
    "remotes": {
        "type": "list",
        "valuesrules": {"type": "dict", "schema": remote_schema}
    },

    "grr": {
        "type": "dict",
        "schema": grr_schema,
    },

    "reference_genome": {"type": "dict", "schema": resource_schema},
    "gene_models": {"type": "dict", "schema": resource_schema},

    "gene_info_db": {"type": "dict", "schema": config_reference_schema},
    "gene_scores_db": {"type": "dict", "schema": gene_scores_db_schema},
    "gene_sets_db": {"type": "dict", "schema": gene_sets_db_schema},
    "default_study_config": {
        "type": "dict",
        "schema": config_reference_schema,
    },
    "gpfjs": {
        "type": "dict",
        "schema": {
            "selected_genotype_data": {
                "type": "list",
                "schema": {"type": "string"}
            },
            "permission_denied_prompt_file": {
                "type": "string",
                # "check_with": validate_existing_path,
                "coerce": "abspath",
            }
        },
    },
    "enrichment": {"type": "dict", "schema": config_reference_schema},
}
