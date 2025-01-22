# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pathlib
from collections.abc import Callable

import pytest

from dae.genotype_storage.genotype_storage import GenotypeStorage
from dae.studies.study import GenotypeData
from dae.testing import (
    setup_pedigree,
    vcf_study,
)
from dae.testing.alla_import import alla_gpf


@pytest.fixture(scope="module")
def imported_vcf_study(
    tmp_path_factory: pytest.TempPathFactory,
    genotype_storage_factory: Callable[[pathlib.Path], GenotypeStorage],
) -> GenotypeData:
    root_path = tmp_path_factory.mktemp("test_query_without_variants")
    genotype_storage = genotype_storage_factory(root_path)
    gpf_instance = alla_gpf(root_path, genotype_storage)
    ped_path = setup_pedigree(
        root_path / "vcf_data" / "in.ped",
        """
        familyId  personId  dadId  momId  sex  status  role
        f1        mom1      0      0      2    1       mom
        f1        dad1      0      0      1    1       dad
        f1        ch1       dad1   mom1   2    2       prb
        f2        mom2      0      0      2    1       mom
        f2        dad2      0      0      1    1       dad
        f2        ch2       dad2   mom2   2    2       prb
        """)

    return vcf_study(
        root_path,
        "test_query_without_variants", ped_path, [],
        gpf_instance)


def test_query_family_variants(
    imported_vcf_study: GenotypeData,
) -> None:
    vs = list(imported_vcf_study.query_variants())
    assert len(vs) == 0


def test_query_summary_variants(
    imported_vcf_study: GenotypeData,
) -> None:
    vs = list(imported_vcf_study.query_summary_variants())
    assert len(vs) == 0
