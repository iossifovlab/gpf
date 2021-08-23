from dae.genomic_resources.gene_models_resource import GeneModelsResource


def test_gene_models_resource(test_grdb):

    res = test_grdb.get_resource(
        "hg19/GATK_ResourceBundle_5777_b37_phiX174/gene_models/refGene_201309")
    assert res is not None

    assert res.get_repo() == test_grdb.repositories[0]

    assert isinstance(res, GeneModelsResource)

    # res.open()
    # assert len(res.gene_models) > 0
