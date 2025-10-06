# pylint: disable=W0621,C0114,C0116,W0212,W0613
import argparse
from typing import cast

import pytest_mock
from dae.annotation.genomic_context import CLIAnnotationContextProvider
from dae.genomic_resources.genomic_context import (
    context_providers_add_argparser_arguments,
    context_providers_init,
    get_genomic_context,
    register_context_provider,
)
from dae.genomic_resources.genomic_context_cli import CLIGenomicContextProvider
from dae.genomic_resources.repository import (
    GenomicResourceProtocolRepo,
    GenomicResourceRepo,
)


def test_cli_genomic_context_reference_genome(
    t4c8_grr: GenomicResourceRepo,
    mocker: pytest_mock.MockerFixture,
) -> None:
    # Given
    grr_dirname = cast(GenomicResourceProtocolRepo, t4c8_grr).proto.get_url()
    assert grr_dirname.startswith("file:///")
    grr_dirname = grr_dirname[7:]

    mocker.patch(
        "dae.genomic_resources.genomic_context."
        "_REGISTERED_CONTEXT_PROVIDERS",
        [])
    mocker.patch(
        "dae.genomic_resources.genomic_context._REGISTERED_CONTEXTS",
        [])

    register_context_provider(CLIGenomicContextProvider())
    register_context_provider(CLIAnnotationContextProvider())

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
    assert context.get_context_keys() <= {
        "reference_genome", "genomic_resources_repository",
        "gene_models",
        "annotation_pipeline",
        "gpf_instance",
    }
