# pylint: disable=W0621,C0114,C0116,W0212,W0613
import textwrap

import pytest
from dae.genomic_resources.repository_factory import (
    build_genomic_resource_repository,
)
from dae.gpf_instance.gpf_instance import GPFInstance
from dae.testing import (
    setup_directories,
    setup_empty_gene_models,
    setup_genome,
    setup_gpf_instance,
)


@pytest.fixture
def gpf_instance(
    tmp_path_factory: pytest.TempPathFactory,
) -> GPFInstance:
    root_path = tmp_path_factory.mktemp("default_storage_test")

    setup_genome(
        root_path / "alla_gpf" / "genome" / "allChr.fa",
        f"""
        >chrA
        {100 * "A"}
        """,
    )
    setup_empty_gene_models(
        root_path / "alla_gpf" / "empty_gene_models" / "empty_genes.txt")

    setup_directories(root_path / "gpf_instance", {
        "gpf_instance.yaml": textwrap.dedent("""
        instance_id: test_instance
        genotype_storage:
            default: alabala
            storages:
            - id: alabala
              storage_type: inmemory
              dir: "%(wd)s/alabala_storage"
        """),
    })

    local_repo = build_genomic_resource_repository({
        "id": "alla_local",
        "type": "directory",
        "directory": str(root_path / "alla_gpf"),
    })

    return setup_gpf_instance(
        root_path / "gpf_instance",
        reference_genome_id="genome",
        gene_models_id="empty_gene_models",
        grr=local_repo,
    )


def test_default_genotype_storage(gpf_instance: GPFInstance) -> None:
    # Given
    gpf = gpf_instance
    # When
    storage = gpf.genotype_storages.get_default_genotype_storage()

    # Then
    assert storage == gpf.genotype_storages.get_genotype_storage("alabala")


def test_get_genotype_storage_with_none(gpf_instance: GPFInstance) -> None:
    # Given
    gpf = gpf_instance

    # When
    storage = gpf.genotype_storages.get_genotype_storage(None)

    # Then
    assert storage == gpf.genotype_storages.get_genotype_storage("alabala")


def test_missing_default_genotype_storage(gpf_instance: GPFInstance) -> None:
    # Given
    gpf = gpf_instance
    genotype_storages = gpf.genotype_storages
    genotype_storages._default_genotype_storage = None

    # When
    with pytest.raises(ValueError, match="default genotype storage not set"):
        genotype_storages.get_default_genotype_storage()
