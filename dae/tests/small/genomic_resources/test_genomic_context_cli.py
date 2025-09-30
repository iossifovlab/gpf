# pylint: disable=W0621,C0114,C0116,W0212,W0613
import argparse
from typing import cast

from dae.genomic_resources.gene_models.gene_models import (
    GeneModels,
)
from dae.genomic_resources.genomic_context_cli import (
    CLIGenomicContextProvider,
)
from dae.genomic_resources.reference_genome import (
    ReferenceGenome,
)
from dae.genomic_resources.repository import (
    GenomicResourceProtocolRepo,
    GenomicResourceRepo,
)


def test_cli_genomic_context_reference_genome(
    t4c8_grr: GenomicResourceRepo,
) -> None:
    # Given
    file_url = cast(GenomicResourceProtocolRepo, t4c8_grr).proto.get_url()
    assert file_url.startswith("file:///")
    grr_dirname = file_url[7:]

    parser = argparse.ArgumentParser(
        description="Test CLI genomic context",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    provider = CLIGenomicContextProvider()
    provider.add_argparser_arguments(parser)

    argv = [
        "--grr-directory", grr_dirname,
        "--ref", "t4c8_genome",
    ]

    # When
    args = parser.parse_args(argv)
    context = provider.init(**vars(args))

    # Then
    assert context is not None

    assert context.get_context_keys() == {
        "reference_genome", "genomic_resources_repository"}

    genome = context.get_reference_genome()
    assert genome is not None
    assert isinstance(genome, ReferenceGenome)
    assert genome.resource.resource_id == "t4c8_genome"


def test_cli_genomic_context_gene_models(
    t4c8_grr: GenomicResourceRepo,
) -> None:
    # Given
    file_url = cast(GenomicResourceProtocolRepo, t4c8_grr).proto.get_url()
    assert file_url.startswith("file:///")
    grr_dirname = file_url[7:]

    parser = argparse.ArgumentParser(
        description="Test CLI genomic context",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    provider = CLIGenomicContextProvider()
    provider.add_argparser_arguments(parser)

    argv = [
        "--grr-directory", grr_dirname,
        "--genes", "t4c8_genes",
    ]

    # When
    args = parser.parse_args(argv)
    context = provider.init(**vars(args))

    # Then
    assert context is not None

    assert context.get_context_keys() == {
        "gene_models", "genomic_resources_repository"}

    gene_models = context.get_gene_models()
    assert gene_models is not None
    assert isinstance(gene_models, GeneModels)
    assert gene_models.resource.resource_id == \
        "t4c8_genes"
