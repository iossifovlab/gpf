# pylint: disable=W0621,C0114,C0116,W0212,W0613
import argparse
import os
import pathlib
from typing import cast

import pytest
from pytest_mock import MockerFixture

from dae.annotation.context import CLIAnnotationContext
from dae.genomic_resources.genomic_context import (
    GenomicContext,
    get_genomic_context,
)
from dae.genomic_resources.repository import (
    GenomicResourceProtocolRepo,
    GenomicResourceRepo,
)


@pytest.fixture
def context_fixture(
        tmp_path: pathlib.Path,
        mocker: MockerFixture) -> GenomicContext:
    conf_dir = str(tmp_path / "genomic_resources")
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


def test_cli_genomic_context_reference_genome(
    t4c8_grr: GenomicResourceRepo,
    context_fixture: GenomicContext,  # noqa
) -> None:
    # Given
    grr_dirname = cast(GenomicResourceProtocolRepo, t4c8_grr).proto.get_url()
    assert grr_dirname.startswith("file:///")
    grr_dirname = grr_dirname[7:]

    parser = argparse.ArgumentParser(
        description="Test CLI genomic context",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    CLIAnnotationContext.add_context_arguments(parser)

    argv = [
        "--grr-directory", grr_dirname,
        "--ref", "t4c8_genome",
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
