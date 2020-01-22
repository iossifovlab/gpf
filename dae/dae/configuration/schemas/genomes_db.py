genome_schema = {
    "chrAllFile": {"type": "string", "path": True},
    "defaultGeneModel": {"type": "string"},
    "geneModel": {
        "type": "dict",
        "valueschema": {
            "type": "dict",
            "schema": {"file": {"type": "string", "path": True}},
        },
    },
}

genomes_db_conf = {
    "genomes": {
        "type": "dict",
        "schema": {"defaultGenome": {"type": "string"}},
    },
    "genome": {"type": "dict", "schema": genome_schema},
    "PARs": {
        "type": "dict",
        "schema": {
            "regions": {"type": "dict", "valueschema": {"type": "string"}}
        },
    },
}
