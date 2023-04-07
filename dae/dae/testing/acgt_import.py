# pylint: disable=W0621,C0114,C0116,W0212,W0613
from dae.testing import \
    setup_genome, setup_empty_gene_models, setup_gpf_instance


def acgt_gpf(root_path, storage=None):
    genome = setup_genome(
        root_path / "acgt_gpf" / "genome" / "allChr.fa",
        f"""
        >chr1
        {25 * "ACGT"}
        >chr2
        {25 * "ACGT"}
        >chr3
        {25 * "ACGT"}
        """
    )

    empty_gene_models = setup_empty_gene_models(
        root_path / "acgt_gpf" / "empty_gene_models" / "empty_genes.txt")
    gpf_instance = setup_gpf_instance(
        root_path / "gpf_instance",
        reference_genome=genome,
        gene_models=empty_gene_models)

    if storage:
        gpf_instance\
            .genotype_storages\
            .register_default_storage(storage)
    return gpf_instance
