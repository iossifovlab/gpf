from dae.gene_scores.implementations.gene_scores_impl import \
    build_gene_score_implementation_from_resource
from dae.genomic_resources import get_resource_implementation_builder, \
    register_implementation


def test_register_implementation() -> None:
    register_implementation(
        "test_gene_score", build_gene_score_implementation_from_resource
    )

    assert get_resource_implementation_builder("test_gene_score") is not None
