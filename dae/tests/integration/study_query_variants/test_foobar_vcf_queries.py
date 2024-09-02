# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pathlib
from collections.abc import Callable

import pytest

from dae.genotype_storage.genotype_storage import GenotypeStorage
from dae.studies.study import GenotypeData
from dae.testing import setup_pedigree, setup_vcf, vcf_study
from dae.testing.foobar_import import foobar_gpf
from dae.utils.regions import Region


@pytest.fixture(scope="module")
def imported_study(
    tmp_path_factory: pytest.TempPathFactory,
    genotype_storage_factory: Callable[[pathlib.Path], GenotypeStorage],
) -> GenotypeData:
    root_path = tmp_path_factory.mktemp("test_foobar_vcf_queries")
    genotype_storage = genotype_storage_factory(root_path)
    gpf_instance = foobar_gpf(root_path, genotype_storage)
    ped_path = setup_pedigree(
        root_path / "vcf_data" / "in.ped",
        """
        familyId personId dadId	 momId	sex status role
        f1       m1       0      0      2   1      mom
        f1       d1       0      0      1   1      dad
        f1       p1       d1     m1     2   2      prb
        """)
    vcf_path = setup_vcf(
        root_path / "vcf_data" / "in.vcf.gz",
        """
        ##fileformat=VCFv4.2
        ##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">
        ##contig=<ID=foo>
        #CHROM POS ID REF ALT QUAL FILTER INFO FORMAT m1  d1  p1
        foo    7   .  A   C   .    .      .    GT     0/1 0/0 0/1
        foo    14  .  C   G   .    .      .    GT     0/0 0/1 0/1
        """)

    return vcf_study(
        root_path,
        "minimal_vcf", ped_path, [vcf_path],
        gpf_instance)


@pytest.mark.parametrize("query,ecount", [
    ({}, 2),
    ({"genes": ["g1"]}, 2),
    ({"genes": ["g2"]}, 0),
    ({"effect_types": ["missense"]}, 1),
    ({"effect_types": ["splice-site"]}, 1),
    ({"regions": [Region("foo", 14, 14)]}, 1),
])
def test_family_queries(
    imported_study: GenotypeData, query: dict,
    ecount: int,
) -> None:

    vs = list(imported_study.query_variants(**query))

    assert len(vs) == ecount


@pytest.mark.parametrize("query,ecount", [
    ({}, 2),
    ({"genes": ["g1"]}, 2),
    ({"genes": ["g2"]}, 0),
    ({"effect_types": ["missense"]}, 1),
    ({"effect_types": ["splice-site"]}, 1),
    ({"regions": [Region("foo", 14, 14)]}, 1),
])
def test_summary_queries(
    imported_study: GenotypeData,
    query: dict,
    ecount: int,
) -> None:

    vs = list(imported_study.query_summary_variants(**query))

    assert len(vs) == ecount
