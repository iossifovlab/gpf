genomic_score_schema = {
    "id ": {"type": "string"},
    "file ": {"type": "string", "path": True},
    "desc ": {"type": "string"},
    "bins ": {"type": "integer"},
    "yscale ": {"type": "string", "allowed": ["linear", "log"]},
    "xscale ": {"type": "string", "allowed": ["linear", "log"]},
    "help_file ": {"type": "string", "path": True},
}


genomic_scores_schema = {
    "genomicScores": {
        "type": "dict",
        "schema": {"scores": {"type": "list", "schema": {"type": "string"}}},
        "allow_unknown": True,
        "valuesrules": {"type": ["list", genomic_score_schema]},
    }
}
