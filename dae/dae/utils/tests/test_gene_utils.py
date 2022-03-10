from dae.utils.gene_utils import GeneSymsMixin
from dae.gene.gene_scores import GeneScore
from dae.configuration.gpf_config_parser import FrozenBox


def test_get_gene_scores_query():
    dummy_enrichment_config = FrozenBox(
        {"testScore": "mock value"}
    )
    kwargs = {
        "geneScores": {
            "score": "testScore",
            "rangeStart": 12,
            "rangeEnd": 34,
        }
    }
    assert GeneSymsMixin.get_gene_scores_query(
        dummy_enrichment_config,
        **kwargs
    ) == ("testScore", 12, 34)


def test_get_gene_scores(mocker):

    dummy_enrichment_config = FrozenBox(
        {"testScore": "mock value"}
    )

    kwargs = {
        "geneScores": {
            "score": "testScore",
            "rangeStart": 12,
            "rangeEnd": 34,
        }
    }

    mocker.patch.object(
        GeneScore,
        "__init__",
        return_value=None
    )
    mocker.patch.object(
        GeneScore,
        "get_genes",
        return_value="mock_return_value"
    )

    assert GeneSymsMixin.get_gene_scores(
        dummy_enrichment_config,
        **kwargs
    ) == "mock_return_value"
