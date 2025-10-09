# pylint: disable=W0621,C0114,C0116,W0212,W0613
import argparse
import pathlib
from typing import cast

import pytest
from dae.genomic_resources.gene_models.gene_models import (
    GeneModels,
)
from dae.genomic_resources.genomic_context import (
    context_providers_add_argparser_arguments,
    context_providers_init,
    get_genomic_context,
    register_context_provider,
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

pytestmark = pytest.mark.usefixtures("clean_genomic_context_providers")


@pytest.fixture
def grr_dirname(t4c8_grr: GenomicResourceRepo) -> str:
    file_url = cast(GenomicResourceProtocolRepo, t4c8_grr).proto.get_url()
    assert file_url.startswith("file:///")
    return file_url[7:]


def test_cli_genomic_context_reference_genome(
    grr_dirname: str,
) -> None:
    # Given

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


def test_cli_genomic_context_provider_reference_genome(
    grr_dirname: str,
) -> None:
    # Given
    register_context_provider(CLIGenomicContextProvider())
    parser = argparse.ArgumentParser(
        description="Test CLI genomic context",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    context_providers_add_argparser_arguments(parser)

    argv = [
        "--grr-directory", grr_dirname,
        "--ref", "t4c8_genome",
    ]

    # When
    args = parser.parse_args(argv)
    context_providers_init(**vars(args))
    context = get_genomic_context()

    # Then
    assert context is not None

    assert context.get_context_keys() == {
        "reference_genome", "genomic_resources_repository"}

    genome = context.get_reference_genome()
    assert genome is not None
    assert isinstance(genome, ReferenceGenome)
    assert genome.resource.resource_id == "t4c8_genome"


def test_cli_genomic_context_gene_models(
    grr_dirname: str,
) -> None:
    # Given
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


def test_cli_genomic_context_provider_gene_models(
    grr_dirname: str,
) -> None:
    # Given
    register_context_provider(CLIGenomicContextProvider())
    parser = argparse.ArgumentParser(
        description="Test CLI genomic context",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    context_providers_add_argparser_arguments(parser)

    argv = [
        "--grr-directory", grr_dirname,
        "--genes", "t4c8_genes",
    ]

    # When
    args = parser.parse_args(argv)
    context_providers_init(**vars(args))
    context = get_genomic_context()

    # Then
    assert context is not None

    assert context.get_context_keys() == {
        "gene_models", "genomic_resources_repository"}

    gene_models = context.get_gene_models()
    assert gene_models is not None
    assert isinstance(gene_models, GeneModels)
    assert gene_models.resource.resource_id == \
        "t4c8_genes"


def test_cli_genomic_context_no_grr(
) -> None:
    # Given
    parser = argparse.ArgumentParser(
        description="Test CLI genomic context",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    provider = CLIGenomicContextProvider()
    provider.add_argparser_arguments(parser)

    argv = [
        "--genes", "t4c8_genes",
    ]

    # When
    args = parser.parse_args(argv)
    context = provider.init(**vars(args))

    # Then
    assert context is None


def test_cli_genomic_context_provider_no_grr(
) -> None:
    # Given
    register_context_provider(CLIGenomicContextProvider())
    parser = argparse.ArgumentParser(
        description="Test CLI genomic context",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    context_providers_add_argparser_arguments(parser)

    argv = [
        "--genes", "t4c8_genes",
    ]

    # When
    args = parser.parse_args(argv)
    context_providers_init(**vars(args))
    context = get_genomic_context()

    # Then
    assert context is not None
    assert context.get_context_keys() == set()


def test_cli_genomic_context_grr_definition(
    t4c8_grr: GenomicResourceRepo,
    tmp_path: pathlib.Path,
) -> None:
    # Given
    (tmp_path / "grr_config.yaml").write_text(
        f"""{t4c8_grr.definition}""")

    parser = argparse.ArgumentParser(
        description="Test CLI genomic context",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    provider = CLIGenomicContextProvider()
    provider.add_argparser_arguments(parser)

    argv = [
        "-g", str(tmp_path / "grr_config.yaml"),
    ]

    # When
    args = parser.parse_args(argv)
    context = provider.init(**vars(args))

    # Then
    assert context is not None

    assert context.get_context_keys() == {
        "genomic_resources_repository"}

    grr = context.get_genomic_resources_repository()
    assert grr is not None
    assert isinstance(grr, GenomicResourceRepo)


def test_cli_genomic_context_providers_grr_definition(
    t4c8_grr: GenomicResourceRepo,
    tmp_path: pathlib.Path,
) -> None:
    # Given
    (tmp_path / "grr_config.yaml").write_text(
        f"""{t4c8_grr.definition}""")

    register_context_provider(CLIGenomicContextProvider())

    parser = argparse.ArgumentParser(
        description="Test CLI genomic context",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    context_providers_add_argparser_arguments(parser)

    argv = [
        "-g", str(tmp_path / "grr_config.yaml"),
    ]

    # When
    args = parser.parse_args(argv)
    context_providers_init(**vars(args))
    context = get_genomic_context()

    # Then
    assert context is not None

    assert context.get_context_keys() == {
        "genomic_resources_repository"}

    grr = context.get_genomic_resources_repository()
    assert grr is not None
    assert isinstance(grr, GenomicResourceRepo)
