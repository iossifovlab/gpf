# pylint: disable=W0621,C0114,C0116,W0212,W0613
import os
import argparse

import pytest

from dae.genomic_resources.genomic_context import \
    CLIGenomicContext, \
    SimpleGenomicContext, \
    SimpleGenomicContextProvider, \
    get_genomic_context, register_context, register_context_provider
from dae.genomic_resources.reference_genome import ReferenceGenome, \
    build_reference_genome_from_resource
from dae.genomic_resources.gene_models import GeneModels, \
    build_gene_models_from_resource
from dae.genomic_resources.repository import GenomicResourceRepo


@pytest.fixture
def context_fixture(fixture_dirname, mocker):
    conf_dir = fixture_dirname("")
    home_dir = os.environ["HOME"]
    mocker.patch("os.environ", {
        "DAE_DB_DIR": conf_dir,
        "HOME": home_dir
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


def test_get_reference_genome_ok(grr_fixture):
    # Given
    res = grr_fixture.get_resource("hg38/GRCh38-hg38/genome")
    genome = build_reference_genome_from_resource(res)

    context = SimpleGenomicContext(
        context_objects={
            "reference_genome": genome
        },
        source=("genome_context", ))

    # When
    genome = context.get_reference_genome()

    # Then
    assert genome is not None
    assert isinstance(genome, ReferenceGenome)
    assert genome.resource.resource_id == "hg38/GRCh38-hg38/genome"


def test_get_reference_genome_missing():
    # Given
    context = SimpleGenomicContext(
        context_objects={
        },
        source=("empty_context", ))

    # When
    genome = context.get_reference_genome()

    # Then
    assert genome is None


def test_get_reference_genome_bad():
    context = SimpleGenomicContext(
        context_objects={
            "reference_genome": "bla"
        },
        source=("bad_genome_context", ))

    with pytest.raises(
            ValueError,
            match="The context returned a wrong type for a reference genome: "
            "<class 'str'>"):
        context.get_reference_genome()


def test_get_gene_models_ok(grr_fixture):
    res = grr_fixture.get_resource(
        "hg38/GRCh38-hg38/gene_models/refSeq_20200330")
    gene_models = build_gene_models_from_resource(res)

    context = SimpleGenomicContext(
        context_objects={
            "gene_models": gene_models
        },
        source=("gene_models", ))

    gene_models = context.get_gene_models()
    assert gene_models is not None
    assert isinstance(gene_models, GeneModels)
    assert gene_models.resource.resource_id == \
        "hg38/GRCh38-hg38/gene_models/refSeq_20200330"


def test_get_gene_models_missing():
    context = SimpleGenomicContext(
        context_objects={
        },
        source=("empty_context", ))
    genes = context.get_gene_models()
    assert genes is None


def test_get_gene_models_bad():
    context = SimpleGenomicContext(
        context_objects={
            "gene_models": "bla"
        },
        source=("bad_genes_context", ))

    with pytest.raises(
            ValueError,
            match="The context returned a wrong type for gene models: "
            "<class 'str'>"):
        context.get_gene_models()


def test_get_grr_ok(grr_fixture):
    # Given
    context = SimpleGenomicContext(
        context_objects={
            "genomic_resources_repository": grr_fixture
        },
        source=("grr_context", ))

    # When
    grr = context.get_genomic_resources_repository()

    # Then
    assert grr is not None
    assert isinstance(grr, GenomicResourceRepo)


def test_get_grr_missing():
    # Given
    context = SimpleGenomicContext(
        context_objects={
        },
        source=("empty_context", ))

    # When
    grr = context.get_genomic_resources_repository()

    # Then
    assert grr is None


def test_get_grr_bad():
    context = SimpleGenomicContext(
        context_objects={
            "genomic_resources_repository": "bla"
        },
        source=("bad_grr_context", ))

    with pytest.raises(
            ValueError,
            match="The context returned a wrong type for GRR: "
            "<class 'str'>"):
        context.get_genomic_resources_repository()


def test_cli_genomic_context_reference_genome(fixture_dirname):
    # Given
    parser = argparse.ArgumentParser(
        description="Test CLI genomic context",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    CLIGenomicContext.add_context_arguments(parser)

    argv = [
        "--grr-directory", fixture_dirname("genomic_resources"),
        "-ref", "hg38/GRCh38-hg38/genome"
    ]

    # When
    args = parser.parse_args(argv)
    context = CLIGenomicContext.context_builder(args)

    # Then
    assert context.get_context_keys() == {
        "reference_genome", "genomic_resources_repository"}

    genome = context.get_reference_genome()
    assert genome is not None
    assert isinstance(genome, ReferenceGenome)
    assert genome.resource.resource_id == "hg38/GRCh38-hg38/genome"


def test_cli_genomic_context_gene_models(fixture_dirname):
    # Given
    parser = argparse.ArgumentParser(
        description="Test CLI genomic context",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    CLIGenomicContext.add_context_arguments(parser)

    argv = [
        "--grr-directory", fixture_dirname("genomic_resources"),
        "-genes", "hg38/GRCh38-hg38/gene_models/refSeq_20200330"
    ]

    # When
    args = parser.parse_args(argv)
    context = CLIGenomicContext.context_builder(args)

    # Then
    assert context.get_context_keys() == {
        "gene_models", "genomic_resources_repository"}

    gene_models = context.get_gene_models()
    assert gene_models is not None
    assert isinstance(gene_models, GeneModels)
    assert gene_models.resource.resource_id == \
        "hg38/GRCh38-hg38/gene_models/refSeq_20200330"


@pytest.fixture
def contexts(grr_fixture):
    gene_models1 = build_gene_models_from_resource(
        grr_fixture.get_resource(
            "hg38/GRCh38-hg38/gene_models/refSeq_20200330"))

    context1 = SimpleGenomicContext(
        context_objects={
            "gene_models": gene_models1
        },
        source=("gene_models1", ))
    gene_models2 = build_gene_models_from_resource(
        grr_fixture.get_resource(
            "hg19/GATK_ResourceBundle_5777_b37_phiX174_short/"
            "gene_models/refGene_201309"))

    context2 = SimpleGenomicContext(
        context_objects={
            "gene_models": gene_models2
        },
        source=("gene_models2", ))
    return context1, context2


def test_register_context(context_fixture, contexts):
    # Given:
    context1, context2 = contexts
    register_context(context1)
    register_context(context2)

    # When
    gene_models = get_genomic_context().get_gene_models()

    # Then
    assert gene_models.resource.resource_id == \
        "hg19/GATK_ResourceBundle_5777_b37_phiX174_short/" \
        "gene_models/refGene_201309"


def test_register_context_provider(context_fixture, contexts):
    # Given:
    context1, context2 = contexts

    register_context_provider(
        SimpleGenomicContextProvider(
            lambda: context2,
            "gene_models2",
            2)
    )
    register_context_provider(
        SimpleGenomicContextProvider(
            lambda: context1,
            "gene_models1",
            1)
    )

    # When
    gene_models = get_genomic_context().get_gene_models()

    # Then
    assert gene_models.resource.resource_id == \
        "hg38/GRCh38-hg38/gene_models/refSeq_20200330"
