from gpf_instance.gpf_instance import get_wgpf_instance

from datasets_api.permissions import IsDatasetAllowed


def expand_gene_set(data, user):
    """Expand gene set to list of gene symbols."""
    if "geneSet" in data:
        data = dict(data)
        gene_sets_collection_id = None
        gene_set_id = None
        denovo_gene_set_spec = None

        query = data.get("geneSet")
        if query is None:
            query = {}
        gene_sets_collection = query.get("geneSetsCollection", None)
        gene_set = query.get("geneSet", None)

        if gene_sets_collection is not None or gene_set is not None:
            gene_sets_collection_id = gene_sets_collection
            gene_set_id = gene_set
            denovo_gene_set_spec = query.get("geneSetsTypes", [])

        gpf_instance = get_wgpf_instance()
        assert gene_sets_collection_id is not None
        if gene_sets_collection_id.endswith("denovo"):
            denovo_gene_sets_db = gpf_instance.denovo_gene_sets_db
            gene_set = denovo_gene_sets_db.get_gene_set(
                gene_set_id,
                denovo_gene_set_spec,
                permitted_datasets=IsDatasetAllowed.permitted_datasets(user),
                collection_id=gene_sets_collection_id
            )
        else:
            gene_sets_db = gpf_instance.gene_sets_db
            gene_set = gene_sets_db.get_gene_set(
                gene_sets_collection_id, gene_set_id
            )
        data["geneSymbols"] = list(gene_set["syms"])
        data["geneSet"] = gene_set["desc"]
    return data
