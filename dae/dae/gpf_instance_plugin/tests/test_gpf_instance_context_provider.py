# pylint: disable=W0621,C0114,C0116,W0212,W0613
import os
import pytest
from dae.genomic_resources.genomic_context import get_genomic_context


@pytest.fixture
def context_fixture(fixture_dirname, mocker):
    conf_dir = fixture_dirname("")
    home_dir = os.environ["HOME"]
    mocker.patch("os.environ", {
        "DAE_DB_DIR": conf_dir,
        "HOME": home_dir
    })
    context = get_genomic_context()
    assert context is not None

    return context


def test_gpf_instance_genomic_context_plugin(context_fixture, fixture_dirname):

    source = context_fixture.get_source()

    assert source[0] == "PriorityGenomicContext"
    assert source[1][0] == "gpf_instance"
    assert source[1][1] == fixture_dirname("")


def test_gpf_instance_context_reference_genome(context_fixture):

    genome = context_fixture.get_reference_genome()

    assert genome is not None
    assert genome.resource.resource_id == \
        "hg19/genomes/GATK_ResourceBundle_5777_b37_phiX174"


def test_gpf_instance_context_gene_models(context_fixture):

    gene_models = context_fixture.get_gene_models()

    assert gene_models is not None
    assert gene_models.resource.resource_id == \
        "hg19/gene_models/refGene_v20190211"


def test_gpf_instance_context_keys(context_fixture):
    keys = context_fixture.get_context_keys()
    assert len(keys) == 5
    assert keys == {
        "gene_models", "reference_genome",
        "genomic_resource_repository", "annotation_pipeline", "gpf_instance"
    }
