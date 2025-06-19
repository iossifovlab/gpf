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
    root_path = tmp_path_factory.mktemp("test_query_by_zygosity_in_status")
    genotype_storage = genotype_storage_factory(root_path)
    gpf_instance = foobar_gpf(root_path, genotype_storage)
    ped_path = setup_pedigree(
        root_path / "vcf_data" / "in.ped",
        """
        familyId personId dadId	 momId	sex status role
        f1       m1       0      0      2   2      mom
        f1       d1       0      0      1   2      dad
        f1       p1       d1     m1     1   2      prb
        f2       m2       0      0      2   1      mom
        f2       d2       0      0      1   1      dad
        f2       p2       d2     m2     1   1      prb
        """)
    vcf_path = setup_vcf(
        root_path / "vcf_data" / "in.vcf.gz",
        """
        ##fileformat=VCFv4.2
        ##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">
        ##contig=<ID=foo>
        #CHROM POS ID REF ALT QUAL FILTER INFO FORMAT m1  d1  p1  m2  d2  p2
        foo    1   .  A   C   .    .      .    GT     1/1 0/0 0/0 0/0 0/0 0/0
        foo    2   .  A   C   .    .      .    GT     0/0 0/0 0/0 1/1 0/0 0/0
        foo    3   .  A   C   .    .      .    GT     0/1 0/0 0/0 0/0 0/0 0/0
        foo    4   .  A   C   .    .      .    GT     0/0 0/0 0/0 0/1 0/0 0/0
        foo    5   .  A   C   .    .      .    GT     0/1 1/1 0/0 0/0 0/0 0/0
        foo    6   .  A   C   .    .      .    GT     0/0 0/0 0/0 0/1 1/1 0/0
        foo    7   .  A   C   .    .      .    GT     0/1 0/0 0/0 1/1 0/0 0/0
        foo    8   .  A   C   .    .      .    GT     1/1 0/0 0/0 0/1 0/0 0/0
        """)

    return vcf_study(
        root_path,
        "test_query_by_zygosity_in_status", ped_path, [vcf_path],
        gpf_instance)


@pytest.mark.gs_duckdb(reason="supported for schema2 duckdb")
@pytest.mark.gs_duckdb_parquet(reason="supported for schema2 duckdb parquet")
@pytest.mark.parametrize(
    "affected_status, expected_positions",
    [
        (
            "affected",
            [1, 3, 5, 7, 8],
        ),
        (
            "affected~homozygous",
            [1, 5, 8],
        ),
        (
            "unaffected~homozygous",
            [2, 6, 7],
        ),
        (
            "affected~heterozygous",
            [3, 5, 7],
        ),
        (
            "unaffected~heterozygous",
            [4, 6, 8],
        ),
        (
            "affected~homozygous or unaffected~homozygous",
            [1, 2, 5, 6, 7, 8],
        ),
        (
            "affected~heterozygous or unaffected~heterozygous",
            [3, 4, 5, 6, 7, 8],
        ),
    ],
)
def test_query_by_zygosity_in_status(
    affected_status: str | None,
    expected_positions: list[int],
    imported_study: GenotypeData,
) -> None:
    vs = list(imported_study.query_variants(
        affected_statuses=affected_status,
    ))
    positions = sorted([v.position for v in vs])
    assert len(positions) == len(expected_positions), positions
    assert positions == expected_positions
