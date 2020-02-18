from dae.configuration.gpf_config_parser import (
    validate_existing_path,
    validate_path,
)

phenotype_schema = {
    "type": "dict",
    "schema": {
        "id": {"type": "string"},
        "name": {"type": "string"},
        "color": {"type": "string"},
    },
}

people_group_schema = {
    "name": {"type": "string"},
    "domain": {"type": "list", "schema": phenotype_schema},
    "default": phenotype_schema,
    "source": {"type": "string"},
}

in_roles_schema = {
    "destination": {"type": "string"},
    "roles": {"type": "list", "schema": {"type": "string"}},
}

genotype_slot_schema = {
    "type": "dict",
    "schema": {
        "name": {"type": "string"},
        "source": {"type": "string"},
        "format": {"type": "string", "default": "%s"},
    },
}

pheno_slot_schema = {
    "type": "dict",
    "schema": {
        "role": {"type": "string"},
        "name": {"type": "string"},
        "source": {"type": "string"},
        "format": {"type": "string", "default": "%s"},
    },
}

pheno_filter_schema = {
    "type": "dict",
    "schema": {
        "filter_type": {"type": "string"},
        "role": {"type": "string"},
        "measure": {"type": "string"},
    },
}

genotype_schema = {
    "name": {"type": "string"},
    "source": {"type": "string"},
    "slots": {"type": "list", "schema": genotype_slot_schema},
}

pheno_schema = {
    "name": {"type": "string"},
    "source": {"type": "string"},
    "slots": {"type": "list", "schema": pheno_slot_schema},
}

standard_criteria_schema = {
    "segments": {"type": "dict", "valuesrules": {"type": "string"}}
}

recurrency_criteria_schema = {
    "type": "dict",
    "schema": {"start": {"type": "integer"}, "end": {"type": "integer"}},
}

background_model_schema = {
    "file": {
        "type": "string",
        "check_with": validate_path,
        "coerce": "abspath",
    },
    "name": {"type": "string"},
    "desc": {"type": "string"},
}

counting_schema = {
    "name": {"type": "string"},
    "desc": {"type": "string"},
}

present_in_role_schema = {
    "name": {"type": "string"},
    "roles": {"type": "list", "schema": {"type": "string"}},
}

pheno_filters_schema = {
    "name": {"type": "string"},
    "measure_type": {"type": "string"},
    "filter": {"type": "list", "schema": pheno_filter_schema},
}


family_schema = {
    "path": {
        "type": "string",
        "check_with": validate_existing_path,
        "coerce": "abspath",
        "required": True,
    },
    "params": {
        "type": "dict",
        "valuesrules": {"type": ["string", "boolean"]},
        "default": {},
    },
}

variants_file = {
    "path": {
        "type": "string",
        "check_with": validate_path,
        "coerce": "abspath",
        "required": True,
    },
    "format": {
        "type": "string",
        "allowed": ["dae", "vcf", "denovo"],
        "required": True,
    },
    "params": {
        "type": "dict",
        "valuesrules": {"type": ["string", "boolean"]},
        "default": {}
    },
}

genotype_storage_schema = {
    "id": {"type": "string"},
    "files": {
        "type": "dict",
        "schema": {
            "pedigree": {"type": "dict", "schema": family_schema},
            "variants": {
                "type": "list",
                "schema": {"type": "dict", "schema": variants_file},
                "default": [],
            },
        },
        "excludes": "tables",
    },
    "tables": {
        "type": "dict",
        "schema": {
            "pedigree": {"type": "string"},
            "variants": {"type": "string"},
        },
        "excludes": "files",
    },
}


study_config_schema = {
    "id": {"type": "string"},
    "name": {"type": "string"},
    "enabled": {"type": "boolean"},
    "work_dir": {
        "type": "string",
        "check_with": validate_existing_path,
        "coerce": "abspath",
        "default": ".",
    },
    "conf_dir": {
        "type": "string",
        "check_with": validate_existing_path,
        "coerce": "abspath",
        "default": ".",
    },
    "phenotype_data": {"type": "string"},
    "phenotype_browser": {"type": "boolean"},
    "phenotype_tool": {"type": "boolean"},
    "description": {"type": "string", "excludes": "description_file"},
    "description_file": {
        "type": "string",
        "check_with": validate_existing_path,
        "coerce": "abspath",
        "excludes": "description",
    },
    "selected_people_groups": {"type": "string"},
    "study_type": {"type": "list", "schema": {"type": "string"}},
    "year": {"type": "list", "schema": {"type": "integer"}},
    "pub_med": {"type": "list", "schema": {"type": "string"}},
    "has_denovo": {"type": "boolean", "default": True},
    "has_transmitted": {"type": "boolean"},
    "has_complex": {"type": "boolean"},
    "has_cnv": {"type": "boolean"},
    "genotype_storage": {
        "type": "dict",
        "schema": genotype_storage_schema,
        "excludes": "studies",
    },
    "studies": {
        "type": "list",
        "schema": {"type": "string"},
        "excludes": "genotype_storage",
    },
    "people_group": {
        "type": "dict",
        "valuesrules": {
            "oneof": [
                {"type": "list", "schema": {"type": "string"}},
                {"type": "dict", "schema": people_group_schema},
            ]
        },
    },
    "genotype_browser": {
        "type": "dict",
        "schema": {
            "enabled": {"type": "boolean", "required": True},
            "has_cnv": {"type": "boolean"},
            "has_complex": {"type": "boolean"},
            "has_family_filters": {"type": "boolean"},
            "has_study_filters": {"type": "boolean"},
            "has_present_in_child": {"type": "boolean"},
            "has_present_in_parent": {"type": "boolean"},
            "has_pedigree_selector": {"type": "boolean"},
            "has_study_types": {"type": "boolean"},
            "has_graphical_preview": {"type": "boolean"},
            "selected_pheno_column_values": {
                "type": "list",
                "schema": {"type": "string"},
                "default": [],
            },
            "family_filters": {
                "type": "list",
                "schema": {"type": "string"},
                "dependencies": {"has_family_filters": True},
            },
            "selected_in_roles_values": {
                "type": "list",
                "schema": {"type": "string"},
                "default": [],
            },
            "inheritance_type_filter": {
                "type": "list",
                "schema": {"type": "string"},
            },
            "selected_inheritance_type_filter_values": {
                "type": "list",
                "schema": {"type": "string"},
                "dependencies": ["inheritance_type_filter"],
            },
            "in_roles": {
                "type": "dict",
                "valuesrules": {"type": "dict", "schema": in_roles_schema},
            },
            "genotype": {
                "type": "dict",
                "valuesrules": {"type": "dict", "schema": genotype_schema},
            },
            "pheno": {
                "type": "dict",
                "valuesrules": {"type": "dict", "schema": pheno_schema},
            },
            "selected_genotype_column_values": {
                "type": "list",
                "schema": {"type": "string"},
                "default": [],
            },
            "preview_columns": {"type": "list", "schema": {"type": "string"}},
            "download_columns": {"type": "list", "schema": {"type": "string"}},
            "present_in_role": {
                "type": "dict",
                "valuesrules": {
                    "type": "dict",
                    "schema": present_in_role_schema,
                },
            },
            "selected_present_in_role_values": {
                "type": "list",
                "schema": {"type": "string"},
                "default": [],
            },
            "pheno_filters": {
                "type": "dict",
                "valuesrules": {
                    "type": "dict",
                    "schema": pheno_filters_schema,
                },
            },
            "selected_pheno_filters_values": {
                "type": "list",
                "schema": {"type": "string"},
                "default": [],
            },
        },
    },
    "common_report": {
        "type": "dict",
        "schema": {
            "enabled": {"type": "boolean", "required": True},
            "selected_people_groups": {
                "type": "list",
                "schema": {"type": "string"},
                "default": [],
            },
            "groups": {
                "type": "list",
                "schema": {
                    "type": "dict",
                    "schema": {
                        "name": {"type": "string"},
                        "people_group_ids": {
                            "type": "list",
                            "schema": {"type": "string"},
                        },
                    },
                },
            },
            "effect_groups": {
                "type": "list",
                "schema": {"type": "string"},
                "default": [],
            },
            "effect_types": {
                "type": "list",
                "schema": {"type": "string"},
                "default": [],
            },
            "families_count_show_id": {"type": "integer"},
            "draw_all_families": {"type": "boolean", "default": False},
            "file_path": {
                "type": "string",
                "check_with": validate_path,
                "coerce": "abspath",
                "default": "common_report.json",
            },
        },
    },
    "denovo_gene_sets": {
        "type": "dict",
        "schema": {
            "enabled": {"type": "boolean", "required": True},
            "selected_people_groups": {
                "type": "list",
                "schema": {"type": "string"},
                "default": [],
            },
            "selected_standard_criterias_values": {
                "type": "list",
                "schema": {"type": "string"},
                "default": [],
            },
            "standard_criterias": {
                "type": "dict",
                "valuesrules": {
                    "type": "dict",
                    "schema": standard_criteria_schema,
                },
            },
            "recurrency_criteria": {
                "type": "dict",
                "schema": {
                    "segments": {
                        "type": "dict",
                        "valuesrules": recurrency_criteria_schema,
                    }
                },
            },
            "gene_sets_names": {"type": "list", "schema": {"type": "string"}},
        },
    },
    "enrichment": {
        "type": "dict",
        "schema": {
            "enabled": {"type": "boolean", "required": True},
            "selected_people_groups": {
                "type": "list",
                "schema": {"type": "string"},
                "default": [],
            },
            "selected_background_values": {
                "type": "list",
                "schema": {"type": "string"},
                "default": [],
            },
            "background": {
                "type": "dict",
                "valuesrules": {
                    "type": "dict",
                    "schema": background_model_schema,
                },
            },
            "default_background_model": {"type": "string"},
            "selected_counting_values": {
                "type": "list",
                "schema": {"type": "string"},
                "default": [],
            },
            "counting": {
                "type": "dict",
                "valuesrules": {"type": "dict", "schema": counting_schema},
            },
            "default_counting_model": {"type": "string"},
            "effect_types": {"type": "list", "schema": {"type": "string"}},
        },
    },
}
