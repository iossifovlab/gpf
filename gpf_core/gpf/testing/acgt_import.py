# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pathlib

from gain.testing.acgt_import import acgt_grr


from gpf.genotype_storage.genotype_storage import GenotypeStorage
from gpf.gpf_instance import GPFInstance
from gpf.testing.setup_helpers import setup_gpf_instance


def acgt_gpf(
        root_path: pathlib.Path,
        storage: GenotypeStorage | None = None) -> GPFInstance:
    local_repo = acgt_grr(root_path)

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
