people_group_schema = {
    "name": {"type": "string"},
    "domain": {"type": "string"},
    "default": {"type": "string"},
    "source": {"type": "string"},
}

in_roles_schema = {
    "destination": {"type": "string"},
    "roles": {"type": "list", "schema": {"type": "string"}},
}


genotype_schema = {
    "name": {"type": "string"},
    "source": {"type": "string"},
    "slots": {"type": "list", "schema": {"type": "string"}},
}


criteria_schema = {"segments": {"type": "list", "schema": {"type": "string"}}}


background_model_schema = {
    "file": {"type": "string", "path": True},
    "name": {"type": "string"},
    "desc": {"type": "string"},
}


counting_schema = {
    "name": {"type": "string"},
    "desc": {"type": "string"},
}


study_config_schema = {
    "genotype_browser ": {"type": "string"},
    "phenotype_data": {"type": "string"},
    "phenotype_browser ": {"type": "string"},
    "phenotype_tool ": {"type": "string"},
    "common_report ": {"type": "string"},
    "description": {"type": "string"},
    "people_groups ": {"type": "string"},
    "genotype_data_study": {
        "type": "dict",
        "schema": {
            "studyType ": {"type": "string"},
            "year": {"type": "integer"},
            "pub_med": {"type": "string"},
            "has_denovo": {"type": "boolean"},
            "has_transmitted": {"type": "boolean"},
            "has_complex": {"type": "boolean"},
            "has_cnv": {"type": "boolean"},
            "genotype_storage": {"type": "string"},
        },
    },
    "genotype_data_group": {
        "type": "dict",
        "schema": {
            "name": {"type": "string"},
            "id": {"type": "string"},
            "studies": {"type": "List", "schema": {"type": "string"}},
        },
    },
    "people_group": {
        "type": "dict",
        "rulesvalues": {"type": "dict", "schema": people_group_schema},
    },
    "genotype_browser": {
        "type": "dict",
        "schema": {
            "has_cnv ": {"type": "boolean"},
            "has_complex ": {"type": "boolean"},
            "has_family_filters": {"type": "boolean"},
            "has_study_filters": {"type": "boolean"},
            "has_present_in_child": {"type": "boolean"},
            "has_present_in_parent": {"type": "boolean"},
            "has_pedigree_selectors ": {"type": "boolean"},
            "selected_pheno_column_values": {
                "type": "list",
                "schema": {"type": "string"},
            },
            "family_filters": {
                "type": "list",
                "schema": {"type": "string"},
                "dependencies": {"has_family_filters": True},
            },
            "selected_selected_in_roles_values": {
                "type": "list",
                "schema": {"type": "string"},
            },
            "inheritance_type_filter": {
                "type": "list",
                "schema": {"type": "string"},
            },
            "selected_inheritance_type_filter_values": {
                "type": "list",
                "schema": {"type": "string"},
                "dependencies": {"inheritance_type_filter": True},
            },
            "in_roles": {
                "type": "dict",
                "rulesvalues": {"type": "dict", "schema": in_roles_schema},
            },
            "genotype": {
                "type": "dict",
                "rulesvalues": {"type": "dict", "schema": genotype_schema},
            },
            "selected_genotype_column_values": {
                "type": "list",
                "schema": {"type": "string"},
            },
            "preview_columns": {"type": "list", "schema": {"type": "string"}},
            "download_columns": {"type": "list", "schema": {"type": "string"}},
        },
    },
    "common_report": {
        "type": "dict",
        "schema": {
            "people_groups": {"type": "list", "schema": {"type": "string"}},
            "groups": {"type": "list", "schema": {"type": "string"}},
            "effect_groups": {"type": "list", "schema": {"type": "string"}},
            "effect_types": {"type": "list", "schema": {"type": "string"}},
        },
    },
    "denovo_gene_sets": {
        "type": "dict",
        "schema": {
            "people_groups": {"type": "list", "schema": {"type": "string"}},
            "standard_criterias": {
                "type": "dict",
                "rulesvalues": {"type": criteria_schema},
            },
            "recurrency_criteria": {
                "type": "dict",
                "rulesvalues": {"type": criteria_schema},
            },
            "gene_sets_names": {"type": "list", "schema": {"type": "string"}},
        },
    },
    "enrichment": {
        "type": "dict",
        "schema": {
            "selected_background_values": {
                "type": "list",
                "schema": {"type": "string"},
            },
            "background": {
                "type": "dict",
                "rulesvalues": {
                    "type": "dict",
                    "schema": background_model_schema,
                },
            },
            "default_background_model": {"type": "string"},
            "selected_counting_values": {
                "type": "list",
                "schema": {"type": "string"},
            },
            "counting": {
                "type": "dict",
                "rulesvalues": {"type": "dict", "schema": counting_schema},
            },
            "default_counting_values": {"type": "string"},
            "effect_types": {"type": "list", "schema": {"type": "string"}},
        },
    },
}
