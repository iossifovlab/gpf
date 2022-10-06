# pylint: disable=W0621,C0114,C0116,W0212,W0613
from dae.testing import \
    setup_genome, setup_gene_models, setup_gpf_instance, \
    vcf_import, vcf_study


# this content follows the 'refflat' gene model format
GMM_CONTENT = """
#geneName name chrom strand txStart txEnd cdsStart cdsEnd exonCount exonStarts exonEnds
g1        tx1  foo   +      3       15    3        13     2         3,7        6,13
g1        tx2  foo   +      3       9     3        6      1         3          6
g2        tx3  bar   -      10      20    12       18     1         12         18
"""  # noqa


def foobar_gpf(root_path, storage=None):
    genome = setup_genome(
        root_path / "foobar_genome" / "chrAll.fa",
        """
            >foo
            NNACCCAAAC
            GGGCCTTCCN
            NNNA
            >bar
            NNGGGCCTTC
            CACGACCCAA
            NN
        """
    )
    genes = setup_gene_models(
        root_path / "foobar_genes" / "genes.txt",
        GMM_CONTENT, fileformat="refflat")

    gpf_instance = setup_gpf_instance(
        root_path / "gpf_instance",
        reference_genome=genome,
        gene_models=genes)

    if storage:
        gpf_instance\
            .genotype_storage_db\
            .register_default_storage(storage)
    return gpf_instance


def foobar_vcf_import(root_path, study_id, ped_path, vcf_path, storage):
    gpf_instance = foobar_gpf(root_path, storage)
    return vcf_import(root_path, study_id, ped_path, [vcf_path], gpf_instance)


def foobar_vcf_study(root_path, study_id, ped_path, vcf_path, storage):
    gpf_instance = foobar_gpf(root_path, storage)
    return vcf_study(root_path, study_id, ped_path, [vcf_path], gpf_instance)
