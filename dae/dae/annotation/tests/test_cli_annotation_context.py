# pylint: disable=W0621,C0114,C0116,W0212,W0613
import os
import argparse
from typing import Callable

import pytest
from pytest_mock import MockerFixture

from dae.annotation.context import CLIAnnotationContext
from dae.genomic_resources.genomic_context import get_genomic_context, \
    GenomicContext


@pytest.fixture
def context_fixture(
        fixture_dirname: Callable[[str], str],
        mocker: MockerFixture) -> GenomicContext:
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


def test_cli_genomic_context_reference_genome(
        fixture_dirname: Callable[[str], str],
        context_fixture: GenomicContext) -> None:
    # Given
    parser = argparse.ArgumentParser(
        description="Test CLI genomic context",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    CLIAnnotationContext.add_context_arguments(parser)

    argv = [
        "--grr-directory", fixture_dirname("genomic_resources"),
        "--ref", "hg38/GRCh38-hg38/genome"
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
