# pylint: disable=W0621,C0114,C0116,W0212,W0613
from collections.abc import Callable

import pytest
from dae.genomic_resources.genomic_context import GenomicContext
from dae.gpf_instance import GPFInstance


@pytest.fixture
def context_fixture(
    t4c8_instance: GPFInstance,
    gpf_instance_genomic_context_fixture: Callable[[GPFInstance], GenomicContext],  # noqa: E501
) -> GenomicContext:
    return gpf_instance_genomic_context_fixture(t4c8_instance)


def test_gpf_instance_genomic_context_plugin(
    context_fixture: GenomicContext,
) -> None:
    source = context_fixture.get_source()
    assert source[0] == "gpf_instance"


def test_gpf_instance_context_reference_genome(
    context_fixture: GenomicContext,
) -> None:
    genome = context_fixture.get_reference_genome()
    assert genome is not None
    assert genome.resource.resource_id == "t4c8_genome"


def test_gpf_instance_context_gene_models(
    context_fixture: GenomicContext,
) -> None:
    gene_models = context_fixture.get_gene_models()
    assert gene_models is not None
    assert gene_models.resource.resource_id == "t4c8_genes"


def test_gpf_instance_context_keys(
    context_fixture: GenomicContext,
) -> None:
    keys = context_fixture.get_context_keys()
    assert len(keys) == 6
    assert keys == {
        "gene_models", "reference_genome",
        "genomic_resources_repository", "annotation_pipeline", "gpf_instance",
        "genotype_storages",
    }
