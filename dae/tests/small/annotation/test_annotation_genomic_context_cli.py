# pylint: disable=W0621,C0114,C0116,W0212,W0613
import argparse
import pathlib
import textwrap
from typing import cast

import pytest
from dae.annotation.annotation_genomic_context_cli import (
    CLIAnnotationContextProvider,
    get_context_pipeline,
)
from dae.genomic_resources.genomic_context import (
    context_providers_add_argparser_arguments,
    context_providers_init,
    get_genomic_context,
    register_context,
    register_context_provider,
)
from dae.genomic_resources.genomic_context_base import (
    SimpleGenomicContext,
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
from dae.genomic_resources.testing import (
    setup_directories,
)

pytestmark = pytest.mark.usefixtures("clean_genomic_context_providers")


@pytest.fixture
def grr_dirname(t4c8_grr: GenomicResourceRepo) -> str:
    file_url = cast(GenomicResourceProtocolRepo, t4c8_grr).proto.get_url()
    assert file_url.startswith("file:///")
    return file_url[7:]


@pytest.fixture
def context_providers(
    clean_genomic_context_providers: None,  # noqa:ARG001
) -> None:
    register_context_provider(CLIGenomicContextProvider())
    register_context_provider(CLIAnnotationContextProvider())


@pytest.fixture
def pipeline_resource(
    grr_dirname: str,
) -> str:
    root_path = pathlib.Path(grr_dirname)
    setup_directories(
        root_path / "pipeline_resource", {
            "genomic_resource.yaml": textwrap.dedent("""
                type: annotation_pipeline
                filename: pipeline.yaml
            """),
            "pipeline.yaml": textwrap.dedent("""
                - effect_annotator
            """),
        },
    )
    return "pipeline_resource"


def test_cli_genomic_context_provider_reference_genome(
    tmp_path: pathlib.Path,
    grr_dirname: str,
    context_providers: None,  # noqa:ARG001
) -> None:
    # Given
    parser = argparse.ArgumentParser(
        description="Test CLI genomic context",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    context_providers_add_argparser_arguments(parser)
    (tmp_path / "pipeline.yaml").write_text(textwrap.dedent(
        """
        - effect_annotator:
            gene_models: t4c8_genes
        """))

    argv = [
        "--grr-directory", grr_dirname,
        "--ref", "t4c8_genome",
        str(tmp_path / "pipeline.yaml"),
    ]

    # When
    args = parser.parse_args(argv)
    context_providers_init(**vars(args))
    context = get_genomic_context()

    # Then
    assert context is not None

    assert context.get_context_keys() == {
        "annotation_pipeline", "reference_genome",
        "genomic_resources_repository"}

    genome = context.get_reference_genome()
    assert genome is not None
    assert isinstance(genome, ReferenceGenome)
    assert genome.resource.resource_id == "t4c8_genome"


def test_cli_genomic_context_provider_reference_genome_and_gene_moels(
    tmp_path: pathlib.Path,
    grr_dirname: str,
    context_providers: None,  # noqa:ARG001
) -> None:
    # Given
    parser = argparse.ArgumentParser(
        description="Test CLI genomic context",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    context_providers_add_argparser_arguments(parser)
    (tmp_path / "pipeline.yaml").write_text(textwrap.dedent(
        """
        - effect_annotator
        """))

    argv = [
        "--grr-directory", grr_dirname,
        "--ref", "t4c8_genome",
        "-G", "t4c8_genes",
        str(tmp_path / "pipeline.yaml"),
    ]

    # When
    args = parser.parse_args(argv)
    context_providers_init(**vars(args))
    context = get_genomic_context()

    # Then
    assert context is not None

    assert context.get_context_keys() == {
        "annotation_pipeline", "reference_genome", "gene_models",
        "genomic_resources_repository"}


def test_cli_genomic_context_provider_no_grr(
    tmp_path: pathlib.Path,
    context_providers: None,  # noqa:ARG001
) -> None:
    # Given
    parser = argparse.ArgumentParser(
        description="Test CLI genomic context",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    context_providers_add_argparser_arguments(parser)
    (tmp_path / "pipeline.yaml").write_text(textwrap.dedent(
        """
        - effect_annotator
        """))

    argv = [
        "--ref", "t4c8_genome",
        "-G", "t4c8_genes",
        str(tmp_path / "pipeline.yaml"),
    ]

    # When
    args = parser.parse_args(argv)
    context_providers_init(**vars(args))
    context = get_genomic_context()

    # Then
    assert context is not None

    assert context.get_context_keys() == set()


def test_cli_genomic_context_provider_pipeline_resource(
    grr_dirname: str,
    context_providers: None,  # noqa:ARG001
    pipeline_resource: str,
) -> None:
    # Given
    parser = argparse.ArgumentParser(
        description="Test CLI genomic context",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    context_providers_add_argparser_arguments(parser)
    argv = [
        "--grr-directory", grr_dirname,
        "--ref", "t4c8_genome",
        "-G", "t4c8_genes",
        pipeline_resource,
    ]

    # When
    args = parser.parse_args(argv)
    context_providers_init(**vars(args))
    context = get_genomic_context()

    # Then
    assert context is not None

    assert context.get_context_keys() == {
        "annotation_pipeline", "reference_genome", "gene_models",
        "genomic_resources_repository"}


def test_cli_genomic_context_provider_bad_pipeline(
    grr_dirname: str,
    context_providers: None,  # noqa:ARG001
) -> None:
    # Given
    parser = argparse.ArgumentParser(
        description="Test CLI genomic context",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    context_providers_add_argparser_arguments(parser)
    argv = [
        "--grr-directory", grr_dirname,
        "--ref", "t4c8_genome",
        "-G", "t4c8_genes",
        "blabla",
    ]

    # When
    args = parser.parse_args(argv)
    with pytest.raises(
            ValueError,
            match=r"The provided argument for an annotation pipeline "):
        context_providers_init(**vars(args))


def test_cli_get_context_bad_pipeline() -> None:
    register_context(SimpleGenomicContext({
        "annotation_pipeline": "blabla",
    }, source=("test", )))

    with pytest.raises(
            TypeError,
            match=r"The annotation pipeline from the genomic context"):
        get_context_pipeline(get_genomic_context())
