from dae.utils.gene_utils import GeneSymsMixin
from dae.gene.weights import GeneWeight
from dae.configuration.gpf_config_parser import FrozenBox


def test_get_gene_weights_query():
    dummy_enrichment_config = FrozenBox(
        {"testWeight": "mock value"}
    )
    kwargs = {
        "geneWeights": {
            "weight": "testWeight",
            "rangeStart": 12,
            "rangeEnd": 34,
        }
    }
    assert GeneSymsMixin.get_gene_weights_query(
        dummy_enrichment_config,
        **kwargs
    ) == ("testWeight", 12, 34)


def test_get_gene_weights(mocker):

    dummy_enrichment_config = FrozenBox(
        {"testWeight": "mock value"}
    )

    kwargs = {
        "geneWeights": {
            "weight": "testWeight",
            "rangeStart": 12,
            "rangeEnd": 34,
        }
    }

    mocker.patch.object(
        GeneWeight,
        "__init__",
        return_value=None
    )
    mocker.patch.object(
        GeneWeight,
        "get_genes",
        return_value="mock_return_value"
    )

    assert GeneSymsMixin.get_gene_weights(
        dummy_enrichment_config,
        **kwargs
    ) == "mock_return_value"
