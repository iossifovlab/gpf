from dae.configuration.gpf_config_parser import validate_existing_path

genome_schema = {
    "chr_all_file": {
        "type": "string",
        "check_with": validate_existing_path,
        "coerce": "abspath",
    },
    "default_gene_models": {"type": "string"},
    "gene_models": {
        "type": "dict",
        "valuesrules": {
            "type": "dict",
            "schema": {
                "file": {
                    "type": "string",
                    "check_with": validate_existing_path,
                    "coerce": "abspath",
                },
                "fileformat": {
                    "type": "string",
                    "allowed": [
                        "default",
                        "gtf",
                        "refseq",
                        "refflat",
                        "ccds",
                        "knowngene",
                        "ucscgenepred",
                        "mito",
                    ],
                },
            },
        },
    },
    "pars": {
        "type": "dict",
        "valuesrules": {"type": "list", "schema": {"type": "string"}},
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
}
