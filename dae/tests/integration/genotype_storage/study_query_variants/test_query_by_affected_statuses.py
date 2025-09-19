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
    root_path = tmp_path_factory.mktemp("test_query_by_affected_statues")
    genotype_storage = genotype_storage_factory(root_path)
    gpf_instance = foobar_gpf(root_path, genotype_storage)
    ped_path = setup_pedigree(
        root_path / "vcf_data" / "in.ped",
        """
        familyId personId dadId	 momId	sex status role
        f1       m1       0      0      2   1      mom
        f1       d1       0      0      1   1      dad
        f1       p1       d1     m1     1   2      prb
        f1       s1       d1     m1     2   1      prb
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
        bar    12  .  A   T   .    .      .    GT     0/0 0/0 1/0 0/0
        """)

    return vcf_study(
        root_path,
        "test_query_by_affected_statues", ped_path, [vcf_path],
        gpf_instance=gpf_instance)


@pytest.mark.no_gs_impala
@pytest.mark.parametrize(
    "affected_statuses,count",
    [
        (None, 4),
        ("unaffected", 3),
        ("affected", 3),
        ("affected or unaffected", 4),
        ("affected and unaffected", 2),
        ("(not affected) and (not unaffected) and (not unspecified)", 0),
    ],
)
def test_query_by_affected_statues(
    affected_statuses: str | None, count: int,
    imported_study: GenotypeData,
) -> None:
    vs = list(imported_study.query_variants(
        affected_statuses=affected_statuses))
    assert len(vs) == count


@pytest.mark.gs_impala
def test_query_by_affected_statuses_does_not_work_schema1(
    imported_study: GenotypeData,
) -> None:
    all_variants = list(imported_study.query_variants())
    all_variants.sort()
    affected_variants = list(imported_study.query_variants(
        affected_statuses="affected",
    ))
    affected_variants.sort()

    unaffected_variants = list(imported_study.query_variants(
        affected_statuses="unaffected",
    ))
    unaffected_variants.sort()

    assert len(all_variants) == len(affected_variants)
    assert len(all_variants) == len(unaffected_variants)

    assert all(
        v1 == v2 for v1, v2
        in zip(all_variants, affected_variants, strict=True)
    )
    assert all(
        v1 == v2 for v1, v2
        in zip(all_variants, unaffected_variants, strict=True)
    )
