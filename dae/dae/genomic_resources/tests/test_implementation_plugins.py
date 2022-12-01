from dae.gene.gene_scores import build_gene_score_collection_from_resource
from dae.genomic_resources import get_resource_implementation_factory, \
    register_implementation


def test_register_implementation():
    register_implementation(
        "test_gene_score", build_gene_score_collection_from_resource
    )

    assert get_resource_implementation_factory("test_gene_score") is not None
