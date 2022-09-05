# pylint: disable=W0621,C0114,C0116,W0212,W0613
import argparse

from dae.annotation.context import CLIAnnotationContext
from dae.genomic_resources.genomic_context import get_genomic_context


def test_cli_genomic_context_reference_genome(fixture_dirname):
    # Given
    parser = argparse.ArgumentParser(
        description="Test CLI genomic context",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    CLIAnnotationContext.add_context_arguments(parser)

    argv = [
        "--grr-directory", fixture_dirname("genomic_resources"),
        "-ref", "hg38/GRCh38-hg38/genome"
    ]

    # When
    args = parser.parse_args(argv)
    CLIAnnotationContext.register(args)

    # Then
    context = get_genomic_context()
    assert context.get_context_keys() <= {
        "reference_genome", "genomic_resources_repository",
        "gene_models",
        "annotation_pipeline",
        "gpf_instance",
    }
