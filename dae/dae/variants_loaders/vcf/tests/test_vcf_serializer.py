# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pathlib

import pytest

from dae.genomic_resources.reference_genome import ReferenceGenome
from dae.genomic_resources.testing import setup_pedigree, setup_vcf
from dae.pedigrees.loader import FamiliesLoader
from dae.variants_loaders.vcf.loader import VcfLoader
from dae.variants_loaders.vcf.serializer import VcfSerializer


@pytest.fixture(scope="module")
def trio_pedigree(
    tmp_path_factory: pytest.TempPathFactory,
) -> pathlib.Path:
    root_path = tmp_path_factory.mktemp("test_vcf_serializer_trio_pedigree")
    return setup_pedigree(root_path / "ped_data" / "in.ped", """
    familyId	personId	dadId	momId	sex	status	role
    f1		    mom1		0	    0	    2	1	    mom
    f1		    dad1		0	    0	    1	1	    dad
    f1		    ch1		    dad1	mom1	2	2	    prb
    """)


@pytest.fixture(scope="module")
def trio_vcf(
    tmp_path_factory: pytest.TempPathFactory,
) -> pathlib.Path:
    root_path = tmp_path_factory.mktemp("test_vcf_serializer_trio_vcf")

    return setup_vcf(root_path / "vcf_data" / "in.vcf", """
    ##fileformat=VCFv4.2
    ##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">
    ##INFO=<ID=INH,Number=1,Type=String,Description="Inheritance">
    ##contig=<ID=chr1>
    #CHROM POS ID REF ALT QUAL FILTER INFO FORMAT mom1 dad1 ch1
    chr1   1   .  T   G   .    .      .    GT     0/0  1/0  1/1
    chr1   5   .  T   G   .    .      .    GT     1/1  1/1  1/0
    chr1   12  .  T   G   .    .      .    GT     1/1  1/1  0/1
    """)


def test_vcf_serializer_simple(
    trio_pedigree: pathlib.Path,
    trio_vcf: pathlib.Path,
    tmp_path: pathlib.Path,
    acgt_genome: ReferenceGenome,
) -> None:
    families = FamiliesLoader(str(trio_pedigree)).load()
    vcf_loader = VcfLoader(
        families,
        [str(trio_vcf)],
        acgt_genome,
    )

    assert vcf_loader is not None
    full_variants = list(vcf_loader.full_variants_iterator())
    assert len(full_variants) == 3

    vcf_serializer = VcfSerializer(
        families, acgt_genome, tmp_path / "out.vcf",
    )
    with vcf_serializer as serializer:
        serializer.serialize(full_variants)

    assert (tmp_path / "out.vcf").exists()

    vcf_check = VcfLoader(
        families,
        [str(tmp_path / "out.vcf")],
        acgt_genome,
    )
    check = list(vcf_check.full_variants_iterator())
    assert len(check) == 3
    for (sv1, fvs1), (sv2, fvs2) in zip(full_variants, check, strict=True):
        assert sv1 == sv2
        assert fvs1 == fvs2
