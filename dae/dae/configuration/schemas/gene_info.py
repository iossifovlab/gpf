gene_weight_schema = {
    "file": {"type ": "string", "path": True},
    "desc ": {"type ": "string"},
    "bins ": {"type ": "integer"},
    "yscale ": {"type ": "string", "allowed": ["linear", "log"]},
    "xscale ": {"type ": "string", "allowed": ["linear", "log"]},
}
gene_term_schema = {
    "file": {"type ": "string", "path": True},
    "webFormatStr": {"type ": "string"},
    "webLabel": {"type ": "string"},
}
gene_info_conf = {
    "geneInfo": {
        "type": "dict",
        "schema": {"geneInfoFile": {"type": "string"}},
    },
    "geneTerms": {"type": "dict", "schema": gene_term_schema},
    "geneWeights": {
        "type": "dict",
        "valuesrules": {"type": ["list", gene_weight_schema]},
        "schema": {
            "weights": {
                "type": "list",
                "required": True,
                "schema": {"type": "string"},
            }
        },
    },
    "chromosomes": {
        "type": "dict",
        "schema": {"file": {"type": "string", "path": True}},
    },
}
