# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pathlib
from collections.abc import Callable

import pytest
from dae.genomic_resources.testing import (
    setup_pedigree,
    setup_vcf,
)
from dae.genotype_storage.genotype_storage import GenotypeStorage
from dae.studies.study import GenotypeData
from dae.testing.alla_import import alla_gpf
from dae.testing.import_helpers import vcf_study


@pytest.fixture(scope="module")
def imported_study(
    tmp_path_factory: pytest.TempPathFactory,
    genotype_storage_factory: Callable[[pathlib.Path], GenotypeStorage],
) -> GenotypeData:
    root_path = tmp_path_factory.mktemp("test_query_by_roles_extended")
    genotype_storage = genotype_storage_factory(root_path)
    gpf_instance = alla_gpf(root_path, genotype_storage)
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
        chr1   1   .  A   C   .    .      .    GT     0/0 0/0 0/1 0/0
        chr1   2   .  A   C   .    .      .    GT     0/0 0/0 0/0 0/1
        chr1   3   .  A   C   .    .      .    GT     0/0 0/0 0/1 0/1
        chr1   4   .  A   C   .    .      .    GT     0/0 1/0 0/0 0/0
        chr1   5   .  A   C   .    .      .    GT     1/0 0/0 0/0 0/0
        chr1   6   .  A   C   .    .      .    GT     1/0 1/0 0/0 0/0
        chr1   7   .  A   C   .    .      .    GT     0/0 1/0 1/0 0/0
        chr1   8   .  A   C   .    .      .    GT     1/0 0/0 1/0 0/0
        chr1   9   .  A   C   .    .      .    GT     1/0 1/0 1/0 0/0
        chr1   10  .  A   C   .    .      .    GT     0/0 1/0 0/0 1/0
        chr1   11  .  A   C   .    .      .    GT     1/0 0/0 0/0 1/0
        chr1   12  .  A   C   .    .      .    GT     1/0 1/0 0/0 1/0
        chr1   13  .  A   C   .    .      .    GT     0/0 1/0 1/0 1/0
        chr1   14  .  A   C   .    .      .    GT     1/0 0/0 1/0 1/0
        chr1   15  .  A   C   .    .      .    GT     1/0 1/0 1/0 1/0
        """)

    return vcf_study(
        root_path,
        "test_query_by_roles_extended", ped_path, [vcf_path],
        gpf_instance=gpf_instance)


@pytest.mark.parametrize(
    "roles,count",
    [
        (None, 15),
        ("prb", 8),
        ("sib", 8),
        ("prb or sib", 12),
        ("prb and sib", 4),
        ("prb and not sib", 4),
        ("mom and sib", 4),
        ("dad and sib", 4),
        ("dad and prb", 4),
        ("sib and not prb", 4),
        ("mom and dad and sib and not prb", 1),
        ("(mom and dad) and ((sib and not prb) or (not sib and prb))", 2),
    ],
)
def test_query_by_roles(
    roles: str | None, count: int, imported_study: GenotypeData,
) -> None:
    vs = list(imported_study.query_variants(
        roles=roles,
    ))
    assert len(vs) == count
