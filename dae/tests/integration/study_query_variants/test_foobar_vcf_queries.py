# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pytest

from dae.utils.regions import Region
from dae.testing import setup_pedigree, setup_vcf, vcf_study

from dae.testing.foobar_import import foobar_gpf


@pytest.fixture(scope="module")
def imported_study(tmp_path_factory, genotype_storage):
    root_path = tmp_path_factory.mktemp(
        f"vcf_path_{genotype_storage.storage_id}")
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
        foo    10  .  C   G   .    .      .    GT     0/0 0/1 0/1
        """)

    study = vcf_study(
        root_path,
        "minimal_vcf", ped_path, [vcf_path],
        gpf_instance)
    return study


@pytest.mark.parametrize("index,query,ecount", [
    (1, {}, 2),
    (2, {"genes": ["g1"]}, 2),
    (3, {"genes": ["g2"]}, 0),
    (4, {"effect_types": ["missense"]}, 1),
    (5, {"effect_types": ["splice-site"]}, 1),
    (6, {"regions": [Region("foo", 10, 10)]}, 1),
])
def test_family_queries(imported_study, index, query, ecount):

    vs = list(imported_study.query_variants(**query))

    assert len(vs) == ecount


@pytest.mark.parametrize("index,query,ecount", [
    (1, {}, 2),
    (2, {"genes": ["g1"]}, 2),
    (3, {"genes": ["g2"]}, 0),
    (4, {"effect_types": ["missense"]}, 1),
    (5, {"effect_types": ["splice-site"]}, 1),
    (6, {"regions": [Region("foo", 10, 10)]}, 1),
])
def test_summary_queries(imported_study, index, query, ecount):

    vs = list(imported_study.query_summary_variants(**query))

    assert len(vs) == ecount
