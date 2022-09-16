# pylint: disable=W0621,C0114,C0116,W0212,W0613

import pytest
import pysam

from dae.utils.variant_utils import mat2str
from dae.utils.regions import Region
from dae.genomic_resources.testing import convert_to_tab_separated, \
    setup_directories
from dae.gpf_instance.gpf_instance import GPFInstance


@pytest.fixture(scope="module")
def best_state_vcf(tmp_path_factory):
    root_path = tmp_path_factory.mktemp("vcf_path")
    in_vcf = convert_to_tab_separated("""
##fileformat=VCFv4.2
##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">
##contig=<ID=1>
#CHROM POS ID REF ALT   QUAL FILTER INFO FORMAT m1  d1  c1
foo    10  .  T   G,C   .    .      .    GT     0/1 0/0 0/0
foo    11  .  T   G,C   .    .      .    GT     0/2 0/0 0/0
foo    12  .  T   G,C   .    .      .    GT     0/0 0/0 0/0
foo    13  .  T   G,C   .    .      .    GT     0/. 0/0 0/0
foo    14  .  T   G,C   .    .      .    GT     0/1 0/2 0/0
foo    15  .  T   G,C,A .    .      .    GT     0/1 0/2 0/3
foo    16  .  T   G,C,A .    .      .    GT     0/1 0/2 0/0
        """)

    in_ped = convert_to_tab_separated(
        """
familyId personId dadId momId sex status role
f1       m1       0     0     2    1     mom
f1       d1       0     0     1    1     dad
f1       c1       d1    m1    2    2     prb
f2       m2       0     0     2    1     mom
f2       d2       0     0     1    1     dad
f2       c2       d2    m2    2    2     prb
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
def import_project(request, tmp_path_factory, best_state_vcf):
    # pylint: disable=import-outside-toplevel
    from ...foobar_import import foobar_vcf_import

    storage_id = request.param
    root_path = tmp_path_factory.mktemp(storage_id)
    ped_path, vcf_path = best_state_vcf

    project = foobar_vcf_import(
        root_path, "best_state", ped_path, vcf_path, storage_id
    )
    return project


@pytest.mark.parametrize("region, exp_num_variants", [
    [Region("foo", 10, 10), 1],  # single allele
    [Region("foo", 12, 12), 0],  # all reference
])
def test_trios_multi(import_project, region, exp_num_variants):
    gpf_instance: GPFInstance = import_project.get_gpf_instance()
    study = gpf_instance.get_genotype_data("best_state")

    variants = list(
        study.query_variants(
            regions=[region],
            return_reference=True,
            return_unknown=True,
        )
    )
    assert len(variants) == exp_num_variants
    for v in variants:
        assert v.best_state.shape == (3, 3)
        assert mat2str(v.best_state) == "122/100/000"
