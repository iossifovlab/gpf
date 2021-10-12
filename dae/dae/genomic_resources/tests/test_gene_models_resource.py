from dae.genomic_resources.gene_models_resource import GeneModelsResource


def test_gene_models_resource(test_grdb):

    res = test_grdb.get_resource(
        "hg19/GATK_ResourceBundle_5777_b37_phiX174/gene_models/refGene_201309")
    assert res is not None

    assert isinstance(res, GeneModelsResource)

    res.open()
    assert len(res.gene_models) == 13


# def test_gene_models_resource_http(test_http_grdb, resources_http_server):

#     res = test_http_grdb.get_resource(
#         "hg19/GATK_ResourceBundle_5777_b37_phiX174/gene_models/refGene_201309")
#     assert res is not None

#     assert isinstance(res, GeneModelsResource)

#     res.open()
#     assert len(res.gene_models) == 13
