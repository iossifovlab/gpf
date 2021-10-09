from dae.genomic_resources.embeded_repository import build_a_test_resource
from dae.genomic_resources.embeded_repository import convert_to_tab_separated
from dae.genomic_resources.gene_models_resource import GeneModelsResource

# this content follows the 'refflat' gene model format
gmmContent = '''
#geneName name chrom strand txStart txEnd cdsStart cdsEnd exonCount exonStarts exonEnds
TP53      tx1  1     +      10      100   12       95     3         10,50,70   15,60,100
TP53      tx1  1     +      10      100   12       95     2         10,70      15,100
POGZ      tx3  17    +      10      100   12       95     3         10,50,70   15,60,100
'''


def test_gene_models_resource_with_format():
    res = build_a_test_resource({
        "genomic_resource.yaml":
            "{type: GeneModels, file: genes.txt, format: refflat}",
        "genes.txt": convert_to_tab_separated(gmmContent)
    })

    print(res.__class__)
    assert res is not None
    assert isinstance(res, GeneModelsResource)

    res.open()
    assert set(res.gene_names()) == {"TP53", "POGZ"}
    assert len(res.transcript_models) == 3


def test_gene_models_resource_with_inferred_format():
    res = build_a_test_resource({
        "genomic_resource.yaml":
            "{type: GeneModels, file: genes.txt}",
        "genes.txt": convert_to_tab_separated(gmmContent)
    })

    print(res.__class__)
    assert res is not None
    assert isinstance(res, GeneModelsResource)

    res.open()
    assert set(res.gene_names()) == {"TP53", "POGZ"}
    assert len(res.transcript_models) == 3


def test_gene_models_resource_with_inferred_format_and_gend_mapping():
    res = build_a_test_resource({
        "genomic_resource.yaml":
            "{type: GeneModels, file: genes.txt, gene_mapping: geneMap.txt}",
        "genes.txt": convert_to_tab_separated(gmmContent),
        "geneMap.txt": convert_to_tab_separated('''
            from   to
            POGZ   gosho
            TP53   pesho
        ''')
    })

    print(res.__class__)
    assert res is not None
    assert isinstance(res, GeneModelsResource)

    res.open()
    assert set(res.gene_names()) == {"gosho", "pesho"}
    assert len(res.transcript_models) == 3


'''
def test_gene_models_resource_http(test_http_grdb, resources_http_server):

    res = test_http_grdb.get_resource(
        "hg19/GATK_ResourceBundle_5777_b37_phiX174/gene_models/refGene_201309")
    assert res is not None

    assert isinstance(res, GeneModelsResource)

    res.open()
    assert len(res.gene_models) == 13
'''
