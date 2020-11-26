from dae.configuration.gpf_config_parser import (
    validate_existing_path,
    validate_path,
)

autism_gene_tool_config = {
    "gene_sets": {"type": "list", "schema": {"type": "string"}},
    "autism_scores": {"type": "list", "schema": {"type": "string"}},
    "protection_scores": {"type": "list", "schema": {"type": "string"}},
    "datasets": {"type": "list", "schema": {"type": "string"}},
    "denovo_criteria": {
        "type": "dict", "valuesrules": {
            "type": "list", "schema": {"type": "string"}
        }
    }
}
