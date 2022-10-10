# pylint: disable=W0621,C0114,C0116,W0212,W0613
from dae.testing import \
    setup_genome, setup_empty_gene_models, setup_gpf_instance, \
    vcf_import, vcf_study


def alla_gpf(root_path, storage=None):
    genome = setup_genome(
        root_path / "alla_gpf" / "genome" / "allChr.fa",
        f"""
        >chrA
        {100 * "A"}
        """
    )

    empty_gene_models = setup_empty_gene_models(
        root_path / "alla_gpf" / "empty_gene_models" / "empty_genes.txt")
    gpf_instance = setup_gpf_instance(
        root_path / "gpf_instance",
        reference_genome=genome,
        gene_models=empty_gene_models)

    if storage:
        gpf_instance\
            .genotype_storage_db\
            .register_default_storage(storage)
    return gpf_instance


def alla_vcf_import(root_path, study_id, ped_path, vcf_path, gpf_instance):
    return vcf_import(root_path, study_id, ped_path, [vcf_path], gpf_instance)


def alla_vcf_study(root_path, study_id, ped_path, vcf_path, gpf_instance):
    return vcf_study(root_path, study_id, ped_path, [vcf_path], gpf_instance)
