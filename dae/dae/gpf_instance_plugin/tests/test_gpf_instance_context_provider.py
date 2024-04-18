# pylint: disable=W0621,C0114,C0116,W0212,W0613
import os
from typing import Callable

import pytest
import pytest_mock

from dae.genomic_resources.genomic_context import (
    GenomicContext,
    get_genomic_context,
)
from dae.gpf_instance import GPFInstance
from dae.gpf_instance_plugin.gpf_instance_context_plugin import (
    init_gpf_instance_genomic_context_plugin,
)


@pytest.fixture()
def context_fixture(
    fixture_dirname: Callable[[str], str],
    mocker: pytest_mock.MockerFixture,
) -> GenomicContext:
    conf_dir = fixture_dirname("")
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

    init_gpf_instance_genomic_context_plugin()
    context = get_genomic_context()
    assert context is not None

    return context


def test_gpf_instance_genomic_context_plugin(
    context_fixture: GenomicContext,
) -> None:

    source = context_fixture.get_source()

    assert source[0] == "PriorityGenomicContext"


def test_gpf_instance_context_reference_genome(
    context_fixture: GenomicContext,
) -> None:

    genome = context_fixture.get_reference_genome()

    assert genome is not None
    assert genome.resource.resource_id == \
        "hg19/GATK_ResourceBundle_5777_b37_phiX174_short/genome"


def test_gpf_instance_context_gene_models(
    context_fixture: GenomicContext,
) -> None:

    gene_models = context_fixture.get_gene_models()

    assert gene_models is not None
    assert gene_models.resource.resource_id == \
        "hg19/GATK_ResourceBundle_5777_b37_phiX174_short/" \
        "gene_models/refGene_201309"


def test_gpf_instance_context_keys(
    context_fixture: GenomicContext,
) -> None:
    keys = context_fixture.get_context_keys()
    assert len(keys) == 5
    assert keys == {
        "gene_models", "reference_genome",
        "genomic_resources_repository", "annotation_pipeline", "gpf_instance",
    }


def test_genomic_context_fixture(
    gpf_instance_genomic_context_fixture: Callable[
        [GPFInstance], GenomicContext],
    t4c8_instance: GPFInstance,
) -> None:
    context = gpf_instance_genomic_context_fixture(t4c8_instance)
    assert context is not None

    context = get_genomic_context()

    ref_genome = context.get_reference_genome()
    assert ref_genome is not None
    assert ref_genome.resource_id == "t4c8_genome"

    gene_models = context.get_gene_models()
    assert gene_models is not None
    assert gene_models.resource_id == "t4c8_genes"
