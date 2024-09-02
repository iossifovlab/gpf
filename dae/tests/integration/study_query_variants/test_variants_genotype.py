# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pathlib
from collections.abc import Callable

import numpy as np
import pytest

from dae.genotype_storage.genotype_storage import GenotypeStorage
from dae.studies.study import GenotypeData
from dae.testing import setup_pedigree, setup_vcf, vcf_study
from dae.testing.alla_import import alla_gpf
from dae.utils.regions import Region


@pytest.fixture(scope="module")
def imported_study(
    tmp_path_factory: pytest.TempPathFactory,
    genotype_storage_factory: Callable[[pathlib.Path], GenotypeStorage],
) -> GenotypeData:
    root_path = tmp_path_factory.mktemp("test_variants_genotype")
    genotype_storage = genotype_storage_factory(root_path)
    gpf_instance = alla_gpf(root_path, genotype_storage)
    ped_path = setup_pedigree(
        root_path / "vcf_data" / "in.ped",
        """
        familyId  personId  dadId  momId  sex  status  role
        f1        mom1      0      0      2    1       mom
        f1        dad1      0      0      1    1       dad
        f1        ch1       dad1   mom1   2    2       prb
        """)
    vcf_path = setup_vcf(
        root_path / "vcf_data" / "in.vcf.gz",
        """
##fileformat=VCFv4.2
##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">
##INFO=<ID=INH,Number=1,Type=String,Description="Inheritance">
##contig=<ID=chrA>
#CHROM POS ID REF ALT   QUAL FILTER INFO FORMAT mom1 dad1 ch1
chrA   1   .  A   G,C   .    .      .    GT     0/0  0/0  ./0
chrA   2   .  A   G,C   .    .      .    GT     1/2  1/.  ./2
chrA   3   .  A   G,C   .    .      .    GT     ./.  ./.  ./2
chrA   4   .  A   G,C   .    .      .    GT     ./.  ./.  ./.
chrA   5   .  A   G,C,T .    .      .    GT     ./.  ./.  ./3
chrA   6   .  A   G,C,T .    .      .    GT     0/0  0/0  0/0
chrA   7   .  A   G     .    .      .    GT     1/0  1/0  0/0
chrA   8   .  A   G     .    .      .    GT     1/0  1/0  1/0
chrA   9   .  A   G,C   .    .      .    GT     2/0  2/0  2/0
        """)

    return vcf_study(
        root_path,
        "inheritance_trio_vcf", pathlib.Path(ped_path),
        [vcf_path],
        gpf_instance,
        project_config_update={
            "input": {
                "vcf": {
                    "include_reference_genotypes": True,
                    "include_unknown_family_genotypes": True,
                    "include_unknown_person_genotypes": True,
                    "denovo_mode": "denovo",
                    "omission_mode": "omission",
                },
            },
            "processing_config": {
                "include_reference": True,
            },
        })


@pytest.mark.parametrize(
    "position, genotype",
    [
        (1, np.array([[0, 0, -1], [0, 0, 0]])),
        (2, np.array([[1, 1, -1], [2, -1, 2]])),
        (3, np.array([[-1, -1, -1], [-1, -1, 2]])),
        (4, np.array([[-1, -1, -1], [-1, -1, -1]])),
        (5, np.array([[-1, -1, -1], [-1, -1, 3]])),
        (6, np.array([[0, 0, 0], [0, 0, 0]])),
        (7, np.array([[1, 1, 0], [0, 0, 0]])),
        (8, np.array([[1, 1, 1], [0, 0, 0]])),
        (9, np.array([[2, 2, 2], [0, 0, 0]])),
    ],
)
def test_variant_gt(
        imported_study: GenotypeData, position: int,
        genotype: np.ndarray) -> None:
    vs = list(imported_study.query_variants(
        regions=[Region("chrA", position, position)],
        return_reference=True,
        return_unknown=True))
    assert len(vs) == 1
    assert np.all(vs[0].gt == genotype)


@pytest.mark.parametrize(
    "position, genotype",
    [
        (1, np.array([[0, 0], [0, 0], [-1, 0]])),
        (2, np.array([[1, 2], [1, -1], [-1, 2]])),
        (3, np.array([[-1, -1], [-1, -1], [-1, 2]])),
        (4, np.array([[-1, -1], [-1, -1], [-1, -1]])),
        (5, np.array([[-1, -1], [-1, -1], [-1, 3]])),
        (6, np.array([[0, 0], [0, 0], [0, 0]])),
        (7, np.array([[1, 0], [1, 0], [0, 0]])),
        (8, np.array([[1, 0], [1, 0], [1, 0]])),
        (9, np.array([[2, 0], [2, 0], [2, 0]])),
    ],
)
def test_variant_genotype(
        imported_study: GenotypeData, position: int,
        genotype: np.ndarray) -> None:
    vs = list(imported_study.query_variants(
        regions=[Region("chrA", position, position)],
        return_reference=True,
        return_unknown=True))
    assert len(vs) == 1
    assert np.all(vs[0].genotype == genotype)


@pytest.mark.parametrize(
    "position, genotype",
    [
        (1, np.array([0, 0, 0, 0, -1, 0])),
        (2, np.array([1, 2, 1, -1, -1, 2])),
        (3, np.array([-1, -1, -1, -1, -1, 2])),
        (4, np.array([-1, -1, -1, -1, -1, -1])),
        (5, np.array([-1, -1, -1, -1, -1, 3])),
        (6, np.array([0, 0, 0, 0, 0, 0])),
        (7, np.array([1, 0, 1, 0, 0, 0])),
        (8, np.array([1, 0, 1, 0, 1, 0])),
        (9, np.array([2, 0, 2, 0, 2, 0])),
    ],
)
def test_variant_genotype_flatten(
        imported_study: GenotypeData, position: int,
        genotype: np.ndarray) -> None:
    vs = list(imported_study.query_variants(
        regions=[Region("chrA", position, position)],
        return_reference=True,
        return_unknown=True))
    assert len(vs) == 1
    assert np.all(vs[0].gt_flatten() == genotype)


@pytest.mark.parametrize(
    "position, members",
    [
        (3, [None, None, "ch1"]),
        (5, [None, None, "ch1"]),
        (7, ["mom1", "dad1", None]),
        (8, ["mom1", "dad1", "ch1"]),
        (9, ["mom1", "dad1", "ch1"]),
    ],
)
def test_variant_in_member(
        imported_study: GenotypeData, position: int,
        members: list[str]) -> None:
    vs = list(imported_study.query_variants(
        regions=[Region("chrA", position, position)],
        return_reference=True,
        return_unknown=True))
    assert len(vs) == 1
    assert len(vs[0].alt_alleles) == 1
    aa = vs[0].family_alt_alleles[0]
    assert aa.variant_in_members == members
