# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pytest

from dae.pedigrees.loader import FamiliesLoader
from dae.testing import acgt_gpf, setup_denovo, setup_pedigree
from dae.variants_loaders.dae.loader import DenovoLoader


@pytest.fixture()
def trio_families(tmp_path_factory):
    root_path = tmp_path_factory.mktemp(
        "denovo_add_chrom_trio_families")
    ped_path = setup_pedigree(
        root_path / "trio_data" / "in.ped",
        """
        familyId personId dadId	 momId	sex status role
        f1       m1       0      0      2   1      mom
        f1       d1       0      0      1   1      dad
        f1       p1       d1     m1     1   2      prb
        """)
    loader = FamiliesLoader(ped_path)
    return loader.load()


@pytest.fixture()
def trio_gpf(tmp_path_factory):
    root_path = tmp_path_factory.mktemp(
        "denovo_acgt_gpf_instance")
    gpf_instance = acgt_gpf(root_path)
    return gpf_instance


@pytest.fixture()
def trio_denovo(tmp_path_factory):
    root_path = tmp_path_factory.mktemp(
        "denovo_add_chrom_trio")
    denovo_path = setup_denovo(
        root_path / "trio_data" / "in.tsv",
        """
          familyId  location  variant    bestState
          f1        1:2       del(2)     2||2||1/0||0||1
          f1        2:2       ins(AA)    2||2||1/0||0||1
        """,
    )
    return denovo_path


@pytest.mark.parametrize(
    "variant_index,chrom,pos,ref,alt",
    [
        (0, "chr1", 1, "ACG", "A"),
        (1, "chr2", 1, "A", "AAA"),
    ],
)
def test_add_chrom_denovo_loader(
        trio_gpf, trio_families, trio_denovo,
        variant_index, chrom, pos, ref, alt):

    loader = DenovoLoader(
        trio_families, str(trio_denovo), trio_gpf.reference_genome,
        params={
            "add_chrom_prefix": "chr",
        })
    alt_alleles = [
        sv.alt_alleles[0] for sv, _ in loader.full_variants_iterator()]
    aa = alt_alleles[variant_index]

    assert aa.chrom == chrom
    assert aa.position == pos
    assert aa.reference == ref
    assert aa.alternative == alt
