import pytest

pytestmark = pytest.mark.usefixtures("gene_info_cache_dir", "calc_gene_sets")


def test_get_person_set_collection_legend(denovo_gene_set_f4):
    dgsl = denovo_gene_set_f4.get_person_set_collection_legend("phenotype")
    print(dgsl)
    assert len(dgsl) == 2


def test_get_person_set_collection_legend_missing(denovo_gene_set_f4):
    dgsl = denovo_gene_set_f4.get_person_set_collection_legend("missing")

    assert len(dgsl) == 0


def test_get_gene_sets_types_legend(denovo_gene_set_f4):
    dgstl = denovo_gene_set_f4.get_gene_sets_types_legend()

    assert len(dgstl) == 1
    assert dgstl[0]["datasetId"] == "f4_trio"
    assert dgstl[0]["datasetName"] == "f4_trio"
    assert dgstl[0]["personSetCollectionId"] == "phenotype"
    assert dgstl[0]["personSetCollectionName"] == "Phenotype"
    assert len(dgstl[0]["personSetCollectionLegend"]) == 2
