# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pathlib

from gain.testing.t4c8_import import t4c8_grr
from gain.genomic_resources.repository import GenomicResourceRepo


from gpf.genotype_storage.genotype_storage import GenotypeStorage
from gpf.gpf_instance import GPFInstance
from gpf.testing.setup_helpers import setup_gpf_instance


def t4c8_gpf(
    root_path: pathlib.Path,
    storage: GenotypeStorage | None = None,
    grr: GenomicResourceRepo | None = None,
) -> GPFInstance:
    if grr is None:
        grr = t4c8_grr(root_path)

    gpf_instance = setup_gpf_instance(
        root_path / "gpf_instance",
        reference_genome_id="t4c8_genome",
        gene_models_id="t4c8_genes",
        grr=grr)

    if storage:
        gpf_instance\
            .genotype_storages\
            .register_default_storage(storage)
    return gpf_instance
