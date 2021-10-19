import pytest

from dae.genomic_resources.gene_models_resource import GeneModelsResource
from dae.genomic_resources.test_tools import build_a_test_resource
from dae.genomic_resources.test_tools import convert_to_tab_separated
from dae.genomic_resources.test_tools import build_test_repos
from dae.genomic_resources.test_tools import run_test_on_all_repos
from dae.genomic_resources.repository import GR_CONF_FILE_NAME

# this content follows the 'refflat' gene model format
gmmContent = '''
#geneName name chrom strand txStart txEnd cdsStart cdsEnd exonCount exonStarts exonEnds
TP53      tx1  1     +      10      100   12       95     3         10,50,70   15,60,100
TP53      tx1  1     +      10      100   12       95     2         10,70      15,100
POGZ      tx3  17    +      10      100   12       95     3         10,50,70   15,60,100
'''  # noqa


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


def test_gene_models_resource_with_inferred_format_and_gene_mapping():
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


def test_against_agains_dirrent_repo_types(tmp_path):
    test_repos = build_test_repos(tmp_path, {
        "one": {
            GR_CONF_FILE_NAME:
            "{type: GeneModels, file: genes.txt}",
            "genes.txt": convert_to_tab_separated(gmmContent)
        }
    })

    run_test_on_all_repos(
        test_repos, "is_gene_model_ok",
        lambda repo: repo.get_resource("one").open()
    )


'''
TODO IVAN How can something like this be done?
@pytest.mark.parametrize("repo", [
    genomic_resource_fixture_repo,
    genomic_resource_fixture_http_repo
])'''


@pytest.mark.fixture_repo
def test_gene_models_resource_http(genomic_resource_fixture_http_repo):

    res = genomic_resource_fixture_http_repo.get_resource(
        "hg19/GATK_ResourceBundle_5777_b37_phiX174/gene_models/refGene_201309")
    assert res is not None

#     assert isinstance(res, GeneModelsResource)

#     res.open()
#     assert len(res.gene_models) == 13
