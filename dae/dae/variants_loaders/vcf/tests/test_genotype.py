# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pathlib

import pytest
import numpy as np

from dae.utils.regions import Region
from dae.testing import setup_pedigree, setup_vcf, \
    vcf_study
from dae.testing.alla_import import alla_gpf
from dae.studies.study import GenotypeData


@pytest.fixture(scope="module")
def a_study(
        tmp_path_factory: pytest.TempPathFactory) -> GenotypeData:
    root_path = tmp_path_factory.mktemp(
        "genotype_tests")
    gpf_instance = alla_gpf(root_path)
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
##contig=<ID=chrA>
#CHROM POS ID REF ALT   QUAL FILTER INFO  FORMAT mom dad ch1 ch2 ch3 gma gpa
chrA   1   .  A   G,C   .    .      .     GT     0/0 0/0 0/0 0/0 0/0 0/0 0/0
chrA   2   .  A   G,C   .    .      .     GT     0/2 0/0 0/0 0/0 0/0 0/0 0/0
chrA   3   .  A   G,C   .    .      .     GT     ./. ./. ./. ./. ./. ./. ./.
chrA   4   .  A   G,C   .    .      .     GT     0/1 0/0 0/0 0/0 0/2 0/0 0/0
chrA   5   .  A   G,C   .    .      .     GT     0/0 0/0 ./. 0/0 0/0 0/0 0/0
chrA   6   .  A   G     .    .      .     GT     0/0 0/0 ./. 0/0 0/0 0/0 0/0
chrA   7   .  A   G     .    .      .     GT     0/0 0/0 ./. 0/0 0/1 0/0 0/0
chrA   8   .  A   G     .    .      .     GT     0/0 0/0 0/0 1/1 0/1 0/0 0/0
chrA   9   .  A   G     .    .      .     GT     0/0 0/0 0/0 0/1 0/0 0/0 1/1
chrA   10  .  A   GC,CC,CT,CC . .   .     GT     2/3 2/2 2/2 2/2 2/2 2/2 2/2
        """)

    study = vcf_study(
        root_path,
        "a", pathlib.Path(ped_path),
        [pathlib.Path(vcf_path)],
        gpf_instance,
        project_config_update={
            "input": {
                "vcf": {
                    "include_reference_genotypes": True,
                    "include_unknown_family_genotypes": True,
                    "include_unknown_person_genotypes": True,
                    "denovo_mode": "denovo",
                    "omission_mode": "omission",
                }
            },
            "processing_config": {
                "include_reference": True
            }
        })
    return study


def test_11540_gt(a_study: GenotypeData) -> None:

    vs = list(a_study.query_variants(regions=[Region("chrA", 2, 2)]))
    assert len(vs) == 1

    v = vs[0]
    assert v.position == 2

    print(v.gt)
    assert np.all(
        np.array([
            [0, 0, 0, 0, 0, 0, 0, ],
            [0, 0, 2, 0, 0, 0, 0, ]
        ])
        == v.gt
    )

    print(v.best_state)
    assert np.all(
        np.array([
            [2, 2, 1, 2, 2, 2, 2, ],
            [0, 0, 0, 0, 0, 0, 0, ],
            [0, 0, 1, 0, 0, 0, 0, ]])
        == v.best_state
    )

    expected_genotype = [
        [0, 0],
        [0, 0],
        [0, 2],
        [0, 0],
        [0, 0],
        [0, 0],
        [0, 0]]
    assert all(eg == g for (eg, g) in zip(expected_genotype, v.genotype))

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
        for (eg, g) in zip(expected_family_genotype, v.family_genotype))


def test_11540_family_alleles(a_study: GenotypeData) -> None:
    vs = list(a_study.query_variants(regions=[Region("chrA", 2, 2)]))
    assert len(vs) == 1

    v = vs[0]
    assert v.position == 2
    assert len(v.alt_alleles) == 1

    aa = v.alt_alleles[0]
    assert aa.allele_index == 2
    assert aa.cshl_variant == "sub(A->C)"

    assert [0, 2] == v.allele_indexes
    assert [0, 1] == v.family_allele_indexes


def test_11548_gt(a_study: GenotypeData) -> None:

    vs = list(a_study.query_variants(regions=[Region("chrA", 10, 10)]))
    assert len(vs) == 1

    v = vs[0]
    assert v.position == 10

    print(v.gt)
    assert np.all(
        np.array([
            [2, 2, 2, 2, 2, 2, 2, ],
            [2, 2, 3, 2, 2, 2, 2, ]
        ])
        == v.gt
    )

    print(v.best_state)
    assert np.all(
        np.array([
            [0, 0, 0, 0, 0, 0, 0, ],
            [0, 0, 0, 0, 0, 0, 0, ],
            [2, 2, 1, 2, 2, 2, 2, ],
            [0, 0, 1, 0, 0, 0, 0, ],
            [0, 0, 0, 0, 0, 0, 0, ],
        ])
        == v.best_state
    )

    expected_genotype = [
        [2, 2],
        [2, 2],
        [2, 3],
        [2, 2],
        [2, 2],
        [2, 2],
        [2, 2]]
    assert all(eg == g for (eg, g) in zip(expected_genotype, v.genotype))

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
        for (eg, g) in zip(expected_family_genotype, v.family_genotype))
