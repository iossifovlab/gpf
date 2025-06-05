# pylint: disable=W0621,C0114,C0116,W0212,W0613
import os
import pathlib

import pytest
import pytest_mock

from dae.genomic_resources.gene_models import (
    GeneModels,
    build_gene_models_from_resource,
)
from dae.genomic_resources.genomic_context import (
    GenomicContext,
    PriorityGenomicContext,
    SimpleGenomicContext,
    get_genomic_context,
    register_context,
)
from dae.genomic_resources.reference_genome import (
    ReferenceGenome,
    build_reference_genome_from_resource,
)
from dae.genomic_resources.repository import (
    GenomicResourceProtocolRepo,
    GenomicResourceRepo,
)


@pytest.fixture
def context_fixture(
    tmp_path: pathlib.Path,
    mocker: pytest_mock.MockerFixture,
) -> GenomicContext:
    conf_dir = str(tmp_path / "conf")
    home_dir = os.environ["HOME"]
    mocker.patch("os.environ", {
        "DAE_DB_DIR": conf_dir,
        "HOME": home_dir,
    })
    mocker.patch(
        "dae.genomic_resources.genomic_context._REGISTERED_CONTEXT_PROVIDERS",
        [])
    mocker.patch(
        "dae.genomic_resources.genomic_context._REGISTERED_CONTEXTS",
        [])
    context = get_genomic_context()
    assert context is not None

    return context


def test_get_reference_genome_ok(
    t4c8_grr: GenomicResourceRepo,
) -> None:
    # Given
    res = t4c8_grr.get_resource("t4c8_genome")
    genome: ReferenceGenome | None = \
        build_reference_genome_from_resource(res)

    context = SimpleGenomicContext(
        context_objects={
            "reference_genome": genome,
        },
        source=("genome_context", ))

    # When
    genome = context.get_reference_genome()

    # Then
    assert genome is not None
    assert isinstance(genome, ReferenceGenome)
    assert genome.resource.resource_id == "t4c8_genome"


def test_get_reference_genome_missing() -> None:
    # Given
    context = SimpleGenomicContext(
        context_objects={
        },
        source=("empty_context", ))

    # When
    genome = context.get_reference_genome()

    # Then
    assert genome is None


def test_get_reference_genome_bad() -> None:
    context = SimpleGenomicContext(
        context_objects={
            "reference_genome": "bla",
        },
        source=("bad_genome_context", ))

    with pytest.raises(
            ValueError,
            match="The context returned a wrong type for a reference genome: "
            "<class 'str'>"):
        context.get_reference_genome()


def test_get_gene_models_ok(
    t4c8_grr: GenomicResourceRepo,
) -> None:
    res = t4c8_grr.get_resource(
        "t4c8_genes")
    gene_models: GeneModels | None = \
        build_gene_models_from_resource(res).load()

    context = SimpleGenomicContext(
        context_objects={
            "gene_models": gene_models,
        },
        source=("gene_models", ))

    gene_models = context.get_gene_models()
    assert gene_models is not None
    assert isinstance(gene_models, GeneModels)
    assert gene_models.resource.resource_id == \
        "t4c8_genes"


def test_get_gene_models_missing() -> None:
    context = SimpleGenomicContext(
        context_objects={
        },
        source=("empty_context", ))
    genes = context.get_gene_models()
    assert genes is None


def test_get_gene_models_bad() -> None:
    context = SimpleGenomicContext(
        context_objects={
            "gene_models": "bla",
        },
        source=("bad_genes_context", ))

    with pytest.raises(
            ValueError,
            match="The context returned a wrong type for gene models: "
            "<class 'str'>"):
        context.get_gene_models()


def test_get_grr_ok(t4c8_grr: GenomicResourceRepo) -> None:
    # Given
    context = SimpleGenomicContext(
        context_objects={
            "genomic_resources_repository": t4c8_grr,
        },
        source=("grr_context", ))

    # When
    grr = context.get_genomic_resources_repository()

    # Then
    assert grr is not None
    assert isinstance(grr, GenomicResourceRepo)


def test_get_grr_missing() -> None:
    # Given
    context = SimpleGenomicContext(
        context_objects={
        },
        source=("empty_context", ))

    # When
    grr = context.get_genomic_resources_repository()

    # Then
    assert grr is None


def test_get_grr_bad() -> None:
    context = SimpleGenomicContext(
        context_objects={
            "genomic_resources_repository": "bla",
        },
        source=("bad_grr_context", ))

    with pytest.raises(
            ValueError,
            match="The context returned a wrong type for GRR: "
            "<class 'str'>"):
        context.get_genomic_resources_repository()


@pytest.fixture
def contexts(
    t4c8_grr: GenomicResourceProtocolRepo,
) -> tuple[SimpleGenomicContext, SimpleGenomicContext]:
    gene_models1 = build_gene_models_from_resource(
        t4c8_grr.get_resource("t4c8_genes")).load()

    context1 = SimpleGenomicContext(
        context_objects={
            "gene_models": gene_models1,
        },
        source=("gene_models1", ))
    gene_models2 = build_gene_models_from_resource(
        t4c8_grr.get_resource(
            "2/t4c8_genes")).load()

    context2 = SimpleGenomicContext(
        context_objects={
            "gene_models": gene_models2,
        },
        source=("gene_models2", ))
    return context1, context2


def test_register_context(
    context_fixture: PriorityGenomicContext,  # noqa: ARG001
    contexts: tuple[SimpleGenomicContext, SimpleGenomicContext],
) -> None:
    # Given:
    context1, context2 = contexts
    register_context(context1)
    register_context(context2)

    # When
    gene_models = get_genomic_context().get_gene_models()

    # Then
    assert gene_models is not None
    assert gene_models.resource.resource_id == "2/t4c8_genes"
