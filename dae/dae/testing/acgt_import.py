# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pathlib
from typing import Optional

from dae.genomic_resources.repository_factory import (
    build_genomic_resource_repository,
)
from dae.genotype_storage.genotype_storage import GenotypeStorage
from dae.gpf_instance import GPFInstance
from dae.testing import (
    setup_empty_gene_models,
    setup_genome,
    setup_gpf_instance,
)


def acgt_gpf(
        root_path: pathlib.Path,
        storage: Optional[GenotypeStorage] = None) -> GPFInstance:
    setup_genome(
        root_path / "acgt_gpf" / "genome" / "allChr.fa",
        f"""
        >chr1
        {25 * "ACGT"}
        >chr2
        {25 * "ACGT"}
        >chr3
        {25 * "ACGT"}
        """,
    )
    setup_empty_gene_models(
        root_path / "acgt_gpf" / "empty_gene_models" / "empty_genes.txt")

    local_repo = build_genomic_resource_repository({
        "id": "acgt_local",
        "type": "directory",
        "directory": str(root_path / "acgt_gpf"),
    })

    gpf_instance = setup_gpf_instance(
        root_path / "gpf_instance",
        reference_genome_id="genome",
        gene_models_id="empty_gene_models",
        grr=local_repo)

    if storage:
        gpf_instance\
            .genotype_storages\
            .register_default_storage(storage)
    return gpf_instance
