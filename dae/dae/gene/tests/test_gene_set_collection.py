import pytest
from dae.gene.gene_sets_db import GeneSetCollection
from dae.gene.tests.conftest import path_to_fixtures


@pytest.mark.parametrize(
    "gene_collection",
    [("main"), (path_to_fixtures("geneInfo/GeneSets/main_candidates.txt"))],
)
def test_gene_set_collection_main(gene_collection, gene_info_config):
    gsc = GeneSetCollection("main", config=gene_info_config)
    assert len(gsc.gene_terms_descriptions) == 1
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
