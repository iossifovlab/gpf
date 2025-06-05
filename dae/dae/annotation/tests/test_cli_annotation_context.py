# pylint: disable=W0621,C0114,C0116,W0212,W0613
import argparse
from typing import cast

from dae.annotation.genomic_context import CLIAnnotationContextProvider
from dae.genomic_resources.repository import (
    GenomicResourceProtocolRepo,
    GenomicResourceRepo,
)


def test_cli_genomic_context_reference_genome(
    t4c8_grr: GenomicResourceRepo,
) -> None:
    # Given
    grr_dirname = cast(GenomicResourceProtocolRepo, t4c8_grr).proto.get_url()
    assert grr_dirname.startswith("file:///")
    grr_dirname = grr_dirname[7:]

    parser = argparse.ArgumentParser(
        description="Test CLI genomic context",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    provider = CLIAnnotationContextProvider()
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
    assert context.get_context_keys() <= {
        "reference_genome", "genomic_resources_repository",
        "gene_models",
        "annotation_pipeline",
        "gpf_instance",
    }
