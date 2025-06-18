# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pathlib

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


def alla_gpf(
    root_path: pathlib.Path, storage: GenotypeStorage | None = None,
) -> GPFInstance:
    setup_genome(
        root_path / "alla_gpf" / "genome" / "allChr.fa",
        f"""
        >chr1
        {100 * "A"}
        >chr2
        {100 * "A"}
        >chr3
        {100 * "A"}
        >chr4
        {100 * "A"}
        >chrX
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
