# pylint: disable=W0621,C0114,C0116,W0212,W0613
from dae.testing import \
    setup_genome, setup_gene_models, setup_gpf_instance


# this content follows the 'refflat' gene model format
GMM_CONTENT = """
#geneName name chrom strand txStart txEnd cdsStart cdsEnd exonCount exonStarts exonEnds
g1        tx1  foo   +      3       15    3        13     2         3,7        6,13
g1        tx2  foo   +      3       9     3        6      1         3          6
g2        tx3  bar   -      3       20    3        18     1         3          17
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
            .genotype_storages\
            .register_default_storage(storage)
    return gpf_instance
