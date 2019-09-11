def test_get_gene_set_legend(denovo_gene_set_f4):
    dgsl = denovo_gene_set_f4.get_gene_set_legend('phenotype')

    assert len(dgsl) == 6


def test_get_gene_set_legend_missing(denovo_gene_set_f4):
    dgsl = denovo_gene_set_f4.get_gene_set_legend('missing')

    assert len(dgsl) == 0


def test_get_gene_sets_types_legend(denovo_gene_set_f4):
    dgstl = denovo_gene_set_f4.get_gene_sets_types_legend()

    assert len(dgstl) == 1
    assert dgstl[0]['datasetId'] == 'f4_trio'
    assert dgstl[0]['datasetName'] == 'f4_trio'
    assert dgstl[0]['peopleGroupId'] == 'phenotype'
    assert dgstl[0]['peopleGroupName'] == 'Phenotype'
    assert len(dgstl[0]['peopleGroupLegend']) == 6
