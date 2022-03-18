from dae.gene.gene_sets_db import GeneSetCollection


def test_gene_set_collection_main(gene_sets_repo):
    resource = gene_sets_repo.get_resource("main")
    gsc = GeneSetCollection.from_resource(resource)
    gene_set = gsc.get_gene_set("main_candidates")
    assert gene_set is not None
    assert gene_set["name"] == "main_candidates"
    assert gene_set["count"] == 9
    assert set(gene_set["syms"]) == {
        "POGZ",
        "CHD8",
        "ANK2",
        "FAT4",
        "NBEA",
        "CELSR1",
        "USP7",
        "GOLGA5",
        "PCSK2",
    }
    assert gene_set["desc"] == "Main Candidates"
