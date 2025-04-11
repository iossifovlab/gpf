# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pathlib
from collections.abc import Callable

import pytest

from dae.genotype_storage.genotype_storage import GenotypeStorage
from dae.query_variants.sql.schema2.sql_query_builder import ZygosityQuery
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
        f1       s1       d1     m1     1   2      sib
        f2       m2       0      0      2   1      mom
        f2       d2       0      0      1   1      dad
        f2       p2       d2     m2     1   1      prb
        f2       s2       d2     m2     1   1      sib
        """)
    vcf_path = setup_vcf(
        root_path / "vcf_data" / "in.vcf.gz",
        """
        ##fileformat=VCFv4.2
        ##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">
        ##contig=<ID=foo>
        #CHROM POS ID REF ALT QUAL FILTER INFO FORMAT m1  d1  p1  s1  m2  d2  p2  s2
        foo    1   .  A   C   .    .      .    GT     1/0 0/0 0/0 0/0 1/0 0/0 0/0 0/0
        foo    2   .  A   C   .    .      .    GT     0/0 1/0 0/0 0/0 0/0 1/0 0/0 0/0
        foo    3   .  A   C   .    .      .    GT     0/0 0/0 1/0 0/0 0/0 0/0 1/0 0/0
        foo    4   .  A   C   .    .      .    GT     0/0 0/0 0/0 1/0 0/0 0/0 0/0 1/0
        foo    5   .  A   C   .    .      .    GT     1/1 0/0 0/0 0/0 1/1 0/0 0/0 0/0
        foo    6   .  A   C   .    .      .    GT     0/0 1/1 0/0 0/0 0/0 1/1 0/0 0/0
        foo    7   .  A   C   .    .      .    GT     0/0 0/0 1/1 0/0 0/0 0/0 1/1 0/0
        foo    8   .  A   C   .    .      .    GT     0/0 0/0 0/0 1/1 0/0 0/0 0/0 1/1
        """)  # noqa: E501

    return vcf_study(
        root_path,
        "test_query_by_zygosity_in_status", ped_path, [vcf_path],
        gpf_instance)


@pytest.mark.gs_duckdb(reason="supported for schema2 duckdb")
@pytest.mark.gs_duckdb_parquet(reason="supported for schema2 duckdb parquet")
@pytest.mark.parametrize(
    "roles, zygosity, expected_positions",
    [
        ("mom", ZygosityQuery(parents_zygosity="heterozygous"), [1, 1]),
        ("dad", ZygosityQuery(parents_zygosity="heterozygous"), [2, 2]),
        ("prb", ZygosityQuery(children_zygosity="heterozygous"), [3, 3]),
        ("sib", ZygosityQuery(children_zygosity="heterozygous"), [4, 4]),
        ("mom", ZygosityQuery(parents_zygosity="homozygous"), [5, 5]),
        ("dad", ZygosityQuery(parents_zygosity="homozygous"), [6, 6]),
        ("prb", ZygosityQuery(children_zygosity="homozygous"), [7, 7]),
        ("sib", ZygosityQuery(children_zygosity="homozygous"), [8, 8]),
    ],
)
def test_query_by_zygosity_in_status(
    roles: str | None,
    zygosity: str,
    expected_positions: list[int],
    imported_study: GenotypeData,
) -> None:
    vs = list(imported_study.query_variants(
        roles=roles,
        zygosity_query=zygosity,
    ))
    positions = sorted([v.position for v in vs])
    assert len(positions) == len(expected_positions), positions
    assert positions == expected_positions
