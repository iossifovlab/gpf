from typing import cast

from datasets_api.permissions import IsDatasetAllowed
from django.contrib.auth.models import User
from gpf_instance.gpf_instance import get_wgpf_instance


def expand_gene_set(data: dict, user: User, instance_id: str) -> dict:
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
        gene_set = expand_gene_syms(
            data, user, instance_id,
        )
        data["geneSymbols"] = list(gene_set["syms"])
        data["geneSet"] = gene_set["desc"]
    return data


def expand_gene_syms(data: dict, user: User, instance_id: str) -> dict:
    """Expand gene set symbols."""
    gene_set = None
    query = data.get("geneSet")
    if query is None:
        query = {}
    gene_sets_collection = query.get("geneSetsCollection", None)
    gene_set = query.get("geneSet", None)
    denovo_gene_set_spec = query.get("geneSetsTypes", [])
    gpf_instance = get_wgpf_instance()
    assert gene_sets_collection is not None
    if gene_sets_collection.endswith("denovo"):
        denovo_gene_sets_db = gpf_instance.denovo_gene_sets_db
        gene_set = denovo_gene_sets_db.get_gene_set(
            gene_set,
            denovo_gene_set_spec,
            permitted_datasets=IsDatasetAllowed.permitted_datasets(
                user, instance_id,
            ),
            collection_id=gene_sets_collection,
        )
    else:
        gene_sets_db = gpf_instance.gene_sets_db
        gene_set = gene_sets_db.get_gene_set(
            gene_sets_collection, gene_set,
        )

    return cast(dict, gene_set)
