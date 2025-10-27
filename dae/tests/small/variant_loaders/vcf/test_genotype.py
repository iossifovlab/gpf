# pylint: disable=W0621,C0114,C0116,W0212,W0613

import numpy as np
import pytest
from dae.genomic_resources.testing import (
    setup_genome,
    setup_pedigree,
    setup_vcf,
)
from dae.pedigrees.loader import FamiliesLoader
from dae.utils.regions import Region
from dae.variants_loaders.vcf.loader import VcfLoader


@pytest.fixture(scope="module")
def study_loader(
    tmp_path_factory: pytest.TempPathFactory,
) -> VcfLoader:
    root_path = tmp_path_factory.mktemp(
        "genotype_tests")
    genome = setup_genome(
        root_path / "genome" / "chr.fa",
        f"""
        >chr1
        {100 * "A"}
        """)

    ped_path = setup_pedigree(
        root_path / "vcf_data" / "in.ped",
        """
familyId personId dadId momId sex status role
f        gpa      0     0     1   1      paternal_grandfather
f        gma      0     0     2   1      paternal_grandmother
f        mom      0     0     2   1      mom
f        dad      gpa   gma   1   1      dad
f        ch1      dad   mom   2   2      prb
f        ch2      dad   mom   2   1      sib
f        ch3      dad   mom   2   1      sib
        """)
    vcf_path = setup_vcf(
        root_path / "vcf_data" / "in.vcf.gz",
        """
##fileformat=VCFv4.2
##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">
##contig=<ID=chr1>
#CHROM POS ID REF ALT   QUAL FILTER INFO  FORMAT mom dad ch1 ch2 ch3 gma gpa
chr1   2   .  A   G,C   .    .      .     GT     0/2 0/0 0/0 0/0 0/0 0/0 0/0
chr1   10  .  A   GC,CC,CT,CC . .   .     GT     2/3 2/2 2/2 2/2 2/2 2/2 2/2
        """)

    families = FamiliesLoader(ped_path).load()
    return VcfLoader(
        families,
        [str(vcf_path)],
        genome,
    )


def test_11540_gt(study_loader: VcfLoader) -> None:
    study_loader.reset_regions([Region("chr1", 2, 2)])
    all_variants = list(study_loader.full_variants_iterator())
    assert len(all_variants) == 1
    _sv, fvs = all_variants[0]
    assert len(fvs) == 1
    v = fvs[0]

    assert v.position == 2

    print(v.gt)
    assert np.all(
        np.array([
            [0, 0, 0, 0, 0, 0, 0],
            [0, 0, 2, 0, 0, 0, 0],
        ])
        == v.gt,
    )

    print(v.best_state)
    assert np.all(
        np.array([
            [2, 2, 1, 2, 2, 2, 2],
            [0, 0, 0, 0, 0, 0, 0],
            [0, 0, 1, 0, 0, 0, 0]])
        == v.best_state,
    )

    expected_genotype = [
        [0, 0],
        [0, 0],
        [0, 2],
        [0, 0],
        [0, 0],
        [0, 0],
        [0, 0]]
    assert all(
        eg == g
        for (eg, g) in zip(expected_genotype, v.genotype, strict=True)
    )

    expected_family_genotype = [
        [0, 0],
        [0, 0],
        [0, 1],
        [0, 0],
        [0, 0],
        [0, 0],
        [0, 0]]
    assert all(
        eg == g
        for (eg, g) in zip(
            expected_family_genotype, v.family_genotype, strict=True))


def test_11540_family_alleles(study_loader: VcfLoader) -> None:
    study_loader.reset_regions([Region("chr1", 2, 2)])
    all_variants = list(study_loader.full_variants_iterator())
    assert len(all_variants) == 1
    _sv, fvs = all_variants[0]
    assert len(fvs) == 1
    v = fvs[0]

    assert v.position == 2
    assert len(v.alt_alleles) == 1

    aa = v.alt_alleles[0]
    assert aa.allele_index == 2
    assert aa.cshl_variant == "sub(A->C)"

    assert v.allele_indexes == [0, 2]
    assert v.family_allele_indexes == [0, 1]


def test_11548_gt(study_loader: VcfLoader) -> None:
    study_loader.reset_regions([Region("chr1", 10, 10)])
    all_variants = list(study_loader.full_variants_iterator())
    assert len(all_variants) == 1
    _sv, fvs = all_variants[0]
    assert len(fvs) == 1
    v = fvs[0]

    assert v.position == 10

    print(v.gt)
    assert np.all(
        np.array([
            [2, 2, 2, 2, 2, 2, 2],
            [2, 2, 3, 2, 2, 2, 2],
        ])
        == v.gt,
    )

    print(v.best_state)
    assert np.all(
        np.array([
            [0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0],
            [2, 2, 1, 2, 2, 2, 2],
            [0, 0, 1, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0],
        ])
        == v.best_state,
    )

    expected_genotype = [
        [2, 2],
        [2, 2],
        [2, 3],
        [2, 2],
        [2, 2],
        [2, 2],
        [2, 2]]
    assert all(
        eg == g
        for (eg, g) in zip(expected_genotype, v.genotype, strict=True))

    expected_family_genotype = [
        [1, 1],
        [1, 1],
        [1, 2],
        [1, 1],
        [1, 1],
        [1, 1],
        [1, 1]]
    assert all(
        eg == g
        for (eg, g) in zip(
            expected_family_genotype, v.family_genotype, strict=True))
