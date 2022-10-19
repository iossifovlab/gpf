# pylint: disable=W0621,C0114,C0116,W0212,W0613
import textwrap

import pytest

from dae.testing import setup_gpf_instance, setup_genome, \
    setup_empty_gene_models, setup_directories


@pytest.fixture
def gpf_instance(tmp_path_factory):
    root_path = tmp_path_factory.mktemp("default_storage_test")

    genome = setup_genome(
        root_path / "alla_gpf" / "genome" / "allChr.fa",
        f"""
        >chrA
        {100 * "A"}
        """
    )
    empty_gene_models = setup_empty_gene_models(
        root_path / "alla_gpf" / "empty_gene_models" / "empty_genes.txt")

    setup_directories(root_path / "gpf_instance", {
        "gpf_instance.yaml": textwrap.dedent("""
        genotype_storage:
            default: alabala
            storages:
            - id: alabala
              storage_type: inmemory
              dir: "%(wd)s/alabala_storage"
        """)
    })

    gpf = setup_gpf_instance(
        root_path / "gpf_instance",
        reference_genome=genome,
        gene_models=empty_gene_models,
    )
    return gpf


def test_default_genotype_storage(gpf_instance):
    # Given
    gpf = gpf_instance
    # When
    storage = gpf.genotype_storages.get_default_genotype_storage()

    # Then
    assert storage == gpf.genotype_storages.get_genotype_storage("alabala")


def test_get_genotype_storage_with_none(gpf_instance):
    # Given
    gpf = gpf_instance

    # When
    storage = gpf.genotype_storages.get_genotype_storage(None)

    # Then
    assert storage == gpf.genotype_storages.get_genotype_storage("alabala")


def test_missing_default_genotype_storage(gpf_instance, mocker):
    # Given
    gpf = gpf_instance
    genotype_storages = gpf.genotype_storages
    genotype_storages._default_genotype_storage = None

    # When
    with pytest.raises(ValueError, match="default genotype storage not set"):
        genotype_storages.get_default_genotype_storage()
