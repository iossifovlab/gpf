# pylint: disable=W0621,C0114,C0116,W0212,W0613

import pytest
import pysam

from dae.utils.regions import Region
from dae.genomic_resources.testing import convert_to_tab_separated, \
    setup_directories
from dae.gpf_instance.gpf_instance import GPFInstance


@pytest.fixture(scope="module")
def minimal_vcf(tmp_path_factory):
    root_path = tmp_path_factory.mktemp("vcf_path")
    in_vcf = convert_to_tab_separated("""
        ##fileformat=VCFv4.2
        ##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">
        ##contig=<ID=foo>
        #CHROM POS ID REF ALT QUAL FILTER INFO FORMAT m1  d1  p1
        foo    7   .  A   C   .    .      .    GT     0/1 0/0 0/1
        foo    10  .  C   G   .    .      .    GT     0/0 0/1 0/1
        """)

    in_ped = convert_to_tab_separated(
        """
            familyId personId dadId	 momId	sex status role
            f1       m1       0      0      2   1      mom
            f1       d1       0      0      1   1      dad
            f1       p1       d1     m1     2   2      prb
        """)

    setup_directories(root_path, {
        "vcf_data": {
            "in.vcf": in_vcf,
            "in.ped": in_ped
        }
    })

    # pylint: disable=no-member
    pysam.tabix_compress(
        str(root_path / "vcf_data" / "in.vcf"),
        str(root_path / "vcf_data" / "in.vcf.gz"))
    pysam.tabix_index(
        str(root_path / "vcf_data" / "in.vcf.gz"), preset="vcf")

    return (root_path / "vcf_data" / "in.ped",
            root_path / "vcf_data" / "in.vcf.gz")


@pytest.fixture(
    scope="module", params=["genotype_impala", "genotype_impala_2"])
def import_project(request, tmp_path_factory, minimal_vcf):
    # pylint: disable=import-outside-toplevel
    from ...foobar_import import foobar_vcf_import

    storage_id = request.param
    root_path = tmp_path_factory.mktemp(storage_id)
    ped_path, vcf_path = minimal_vcf

    project = foobar_vcf_import(
        root_path, "minimal_vcf", ped_path, vcf_path, storage_id)
    return project


@pytest.mark.parametrize("index, query,ecount", [
    (1, {}, 2),
    (2, {"genes": ["g1"]}, 2),
    (3, {"genes": ["g2"]}, 0),
    (4, {"effect_types": ["missense"]}, 1),
    (5, {"effect_types": ["splice-site"]}, 1),
    (6, {"regions": [Region("foo", 10, 10)]}, 1),
])
def test_family_queries(import_project, index, query, ecount):
    gpf_instance: GPFInstance = import_project.get_gpf_instance()
    gpf_instance.reload()

    assert gpf_instance.get_genotype_data_ids() == ["minimal_vcf"]

    study = gpf_instance.get_genotype_data("minimal_vcf")
    vs = list(study.query_variants(**query))

    assert len(vs) == ecount


@pytest.mark.parametrize("index,query,ecount", [
    (1, {}, 2),
    # FIXME fix in schema 2 and uncomment
    # (2, {"genes": ["g1"]}, 2),
    (3, {"genes": ["g2"]}, 0),
    # (4, {"effect_types": ["missense"]}, 1),
    # (5, {"effect_types": ["splice-site"]}, 1),
    (6, {"regions": [Region("foo", 10, 10)]}, 1),
])
def test_summary_queries(import_project, index, query, ecount):
    gpf_instance: GPFInstance = import_project.get_gpf_instance()
    gpf_instance.reload()

    assert gpf_instance.get_genotype_data_ids() == ["minimal_vcf"]

    study = gpf_instance.get_genotype_data("minimal_vcf")
    vs = list(study.query_summary_variants(**query))

    assert len(vs) == ecount
