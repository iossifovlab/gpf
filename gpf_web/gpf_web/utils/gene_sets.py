from typing import Any


def get_denovo_gene_set_spec(gene_sets_types: list[Any]) -> dict[str, Any]:
    """Convert typescript style gene sets types into python dict."""
    denovo_gene_set_spec = {}
    for gene_sets_type in gene_sets_types:
        collections = {}
        for collection in gene_sets_type["collections"]:
            collections[collection["personSetId"]] = collection["types"]
        denovo_gene_set_spec[gene_sets_type["datasetId"]] = collections

    return denovo_gene_set_spec
