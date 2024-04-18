# pylint: disable=W0621,C0114,C0116,W0212,W0613
import textwrap

import pytest

from dae.genomic_resources.repository_factory import (
    build_genomic_resource_repository,
)
from dae.testing import (
    setup_directories,
    setup_empty_gene_models,
    setup_genome,
    setup_gpf_instance,
)


def test_internal_genotype_storage(
    tmp_path_factory: pytest.TempPathFactory,
) -> None:
    # Given
    root_path = tmp_path_factory.mktemp("internal_storage_test")

    setup_genome(
        root_path / "alla_gpf" / "genome" / "allChr.fa",
        f"""
        >chrA
        {100 * "A"}
        """,
    )
    setup_empty_gene_models(
        root_path / "alla_gpf" / "empty_gene_models" / "empty_genes.txt")
    local_repo = build_genomic_resource_repository({
        "id": "alla_local",
        "type": "directory",
        "directory": str(root_path / "alla_gpf"),
    })
    gpf = setup_gpf_instance(
        root_path / "gpf_instance",
        reference_genome_id="genome",
        gene_models_id="empty_gene_models",
        grr=local_repo,
    )

    # When
    internal_storage = gpf.genotype_storages.get_genotype_storage("internal")

    # Then
    assert internal_storage.storage_type == "inmemory"
    assert internal_storage.storage_config["dir"] == \
        str(root_path / "gpf_instance" / "internal_storage")
    assert gpf.genotype_storages.get_default_genotype_storage() == \
        internal_storage


def test_internal_genotype_storage_with_other_storages(
    tmp_path_factory: pytest.TempPathFactory,
) -> None:
    # Given
    root_path = tmp_path_factory.mktemp("internal_storage_test")

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

    gpf = setup_gpf_instance(
        root_path / "gpf_instance",
        reference_genome_id="genome",
        gene_models_id="empty_gene_models",
        grr=local_repo,
    )

    # When
    internal_storage = gpf.genotype_storages.get_genotype_storage("internal")

    # Then
    assert internal_storage.storage_type == "inmemory"
    assert internal_storage.storage_config["dir"] == \
        str(root_path / "gpf_instance" / "internal_storage")
    assert gpf.genotype_storages.get_default_genotype_storage() != \
        internal_storage
