# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pathlib

from gain.genomic_resources.repository_factory import (
    build_genomic_resource_repository,
)
from gain.testing.foobar_import import foobar_genes, foobar_genome

from gpf.genotype_storage.genotype_storage import GenotypeStorage
from gpf.gpf_instance.gpf_instance import GPFInstance
from gpf.testing.setup_helpers import setup_gpf_instance


def foobar_gpf(
        root_path: pathlib.Path,
        storage: GenotypeStorage | None = None) -> GPFInstance:
    foobar_genome(root_path)
    foobar_genes(root_path)
    local_repo = build_genomic_resource_repository({
        "id": "foobar_local",
        "type": "directory",
        "directory": str(root_path),
    })

    gpf_instance = setup_gpf_instance(
        root_path / "gpf_instance",
        reference_genome_id="foobar_genome",
        gene_models_id="foobar_genes",
        grr=local_repo)

    if storage:
        gpf_instance\
            .genotype_storages\
            .register_default_storage(storage)
    return gpf_instance
