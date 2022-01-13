from dae.configuration.gpf_config_parser import validate_existing_path

gene_weight_schema = {
    "file": {
        "type": "string",
        "check_with": validate_existing_path,
        "coerce": "abspath",
    },
    "desc": {"type": "string"},
    "bins": {"type": "integer"},
    "yscale": {"type": "string", "allowed": ["linear", "log"]},
    "xscale": {"type": "string", "allowed": ["linear", "log"]},
}

gene_term_schema = {
    "file": {
        "type": "string",
        "check_with": validate_existing_path,
        "coerce": "abspath",
    },
    "web_format_str": {"type": "string"},
    "web_label": {"type": "string"},
}

gene_info_conf = {
    "conf_dir": {
        "type": "string",
        "check_with": validate_existing_path,
        "coerce": "abspath",
        "required": True,
    },
    "gene_info": {
        "type": "dict",
        "schema": {
            "gene_info_file": {
                "type": "string",
                "check_with": validate_existing_path,
                "coerce": "abspath",
            },
            "selected_gene_weights": {
                "type": "list",
                "schema": {"type": "string"},
                "default": [],
            },
        },
    },
    "gene_terms": {
        "type": "dict",
        "valuesrules": {"type": "dict", "schema": gene_term_schema},
    },
    "gene_weights": {
        "type": "dict",
        "valuesrules": {"type": "dict", "schema": gene_weight_schema},
    },
    "chromosomes": {
        "type": "dict",
        "schema": {
            "file": {
                "type": "string",
                "check_with": validate_existing_path,
                "coerce": "abspath",
            }
        },
    },
}
