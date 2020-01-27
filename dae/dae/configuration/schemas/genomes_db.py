from dae.configuration.gpf_config_parser import validate_path

genome_schema = {
    "chr_all_file": {
        "type": "string",
        "check_with": validate_path,
        "coerce": "abspath",
    },
    "default_gene_model": {"type": "string"},
    "gene_model": {
        "type": "dict",
        "valuesrules": {
            "type": "dict",
            "schema": {
                "file": {
                    "type": "string",
                    "check_with": validate_path,
                    "coerce": "abspath",
                }
            },
        },
    },
}

genomes_db_conf = {
    "genomes": {
        "type": "dict",
        "schema": {"default_genome": {"type": "string"}},
    },
    "genome": {
        "type": "dict",
        "valuesrules": {"type": "dict", "schema": genome_schema},
    },
    "PARs": {
        "type": "dict",
        "schema": {
            "regions": {
                "type": "dict",
                "valuesrules": {"type": "list", "schema": {"type": "string"}},
            }
        },
    },
}
