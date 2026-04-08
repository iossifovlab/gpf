# pylint: disable=W0621,C0114,C0116,W0212,W0613
from gain.gene_sets.gene_set import (
    GeneSetCollection,
    build_gene_set_collection_from_resource_id,
)
from gain.genomic_resources.repository import (
    GenomicResourceRepo,
)


def test_gene_set_collection_main(
    gene_sets_repo_in_memory: GenomicResourceRepo,
) -> None:
    resource = gene_sets_repo_in_memory.get_resource("main")
    gsc = GeneSetCollection(resource)
    gsc.load()

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


def test_build_gene_set_collection_from_resource_id(
    gene_sets_repo_in_memory: GenomicResourceRepo,
) -> None:
    gsc = build_gene_set_collection_from_resource_id(
        "main",
        gene_sets_repo_in_memory,
    )
    gsc.load()
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
