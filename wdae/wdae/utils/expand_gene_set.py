from typing import cast

from gpf_instance.gpf_instance import get_wgpf_instance

from utils.gene_sets import get_denovo_gene_set_spec


def expand_gene_set(data: dict) -> dict:
    """Expand gene set to list of gene symbols."""
    if "geneSet" in data:
        gene_sets_collection_id = None

        query = data.get("geneSet")
        if query is None:
            query = {}
        gene_sets_collection = query.get("geneSetsCollection", None)
        gene_set = query.get("geneSet", None)

        if gene_sets_collection is not None or gene_set is not None:
            gene_sets_collection_id = gene_sets_collection

        assert gene_sets_collection_id is not None
        gene_set = expand_gene_syms(data)
        gene_symbols = set(
            data.get("geneSymbols", []),
        ).union(set(gene_set["syms"]))
        data["geneSymbols"] = list(gene_symbols)
        data["geneSetDesc"] = gene_set["desc"]

    return data


def expand_gene_syms(data: dict) -> dict:
    """Expand gene set symbols."""
    gene_set = None
    query = data.get("geneSet")
    if query is None:
        query = {}
    gene_sets_collection = query.get("geneSetsCollection", None)
    gene_set = query.get("geneSet", None)

    denovo_gene_sets_types = get_denovo_gene_set_spec(
        query.get("geneSetsTypes", []),
    )

    gpf_instance = get_wgpf_instance()
    assert gene_sets_collection is not None
    if gene_sets_collection.endswith("denovo"):
        denovo_gene_sets_db = gpf_instance.denovo_gene_sets_db
        gene_set = denovo_gene_sets_db.get_gene_set(
            gene_set,
            denovo_gene_sets_types,
            collection_id=gene_sets_collection,
        )
    else:
        gene_sets_db = gpf_instance.gene_sets_db
        gene_set = gene_sets_db.get_gene_set(
            gene_sets_collection, gene_set,
        )

    return cast(dict, gene_set)
