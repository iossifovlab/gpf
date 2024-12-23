# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pathlib
from collections.abc import Callable

import pytest

from dae.genotype_storage.genotype_storage import GenotypeStorage
from dae.studies.study import GenotypeData
from dae.testing import setup_pedigree, setup_vcf, vcf_study
from dae.testing.foobar_import import foobar_gpf


@pytest.fixture(scope="module")
def imported_study(
    tmp_path_factory: pytest.TempPathFactory,
    genotype_storage_factory: Callable[[pathlib.Path], GenotypeStorage],
) -> GenotypeData:
    root_path = tmp_path_factory.mktemp("test_query_by_roles")
    genotype_storage = genotype_storage_factory(root_path)
    gpf_instance = foobar_gpf(root_path, genotype_storage)
    ped_path = setup_pedigree(
        root_path / "vcf_data" / "in.ped",
        """
        familyId personId dadId	 momId	sex status role
        f1       m1       0      0      2   1      mom
        f1       d1       0      0      1   1      dad
        f1       p1       d1     m1     1   2      prb
        f1       s1       d1     m1     2   1      sib
        """)
    vcf_path = setup_vcf(
        root_path / "vcf_data" / "in.vcf.gz",
        """
        ##fileformat=VCFv4.2
        ##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">
        ##contig=<ID=foo>
        #CHROM POS ID REF ALT QUAL FILTER INFO FORMAT m1  d1  p1  s1
        foo    7   .  A   C   .    .      .    GT     0/1 0/0 0/1 0/0
        foo    10  .  C   G   .    .      .    GT     0/0 0/1 0/1 0/0
        bar    11  .  C   G   .    .      .    GT     1/0 0/0 0/0 0/1
        bar    12  .  A   T   .    .      .    GT     0/0 1/0 1/0 0/0
        bar    13  .  C   T   .    .      .    GT     0/0 1/0 1/0 1/0
        """)

    return vcf_study(
        root_path,
        "minimal_vcf", ped_path, [vcf_path],
        gpf_instance)


@pytest.mark.parametrize(
    "roles,count",
    [
        (None, 5),
        ("prb", 4),
        ("prb or sib", 5),
        ("prb and sib", 1),
        ("prb and not sib", 3),
        ("mom and sib", 1),
        ("dad and sib", 1),
        ("dad and prb", 3),
        ("sib and not prb", 1),
    ],
)
def test_query_by_roles(
    roles: str | None, count: int, imported_study: GenotypeData,
) -> None:
    vs = list(imported_study.query_variants(roles=roles))
    assert len(vs) == count


@pytest.mark.parametrize(
    "person_ids,count",
    [
        (None, 5),
        ({"m1"}, 2),
        ({"d1"}, 3),
        ({"p1"}, 4),
        ({"s1"}, 2),
    ],
)
def test_query_person_id(
    person_ids: set[str] | None, count: int,
    imported_study: GenotypeData,
) -> None:
    vs = list(imported_study.query_variants(person_ids=person_ids))
    assert len(vs) == count


@pytest.mark.parametrize(
    "family_ids,count",
    [
        (None, 5),
        ({"f1"}, 5),
    ],
)
def test_query_family_id(
    family_ids: set[str] | None, count: int,
    imported_study: GenotypeData,
) -> None:
    vs = list(imported_study.query_variants(family_ids=family_ids))
    assert len(vs) == count

# TODO: add _status
