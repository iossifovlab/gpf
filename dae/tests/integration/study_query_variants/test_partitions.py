# pylint: disable=W0621,C0114,C0116,W0212,W0613
import textwrap
import pytest

from dae.testing import setup_pedigree, setup_vcf, vcf_study
from dae.testing.foobar_import import foobar_gpf
from dae.utils.regions import Region



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
    
    partition_def = textwrap.dedent("""
      partition_description:
        region_bin:
            chromosomes: ['foo', 'bar']
            region_length: 100
    """)
    
    partition_def = textwrap.dedent("""
      partition_description:
        region_bin:
            chromosomes: ['foo', 'bar']
            region_length: 100
        family_bin:
            family_bin_size: 2
        frequency_bin:
            rare_boundary: 5
        coding_bin:
            coding_effect_types: "splice-site,frame-shift,nonsense,no-frame-shift-newStop,noStart,noEnd,missense,no-frame-shift,CDS,synonymous,coding_unknown,regulatory,3'UTR,5'UTR"
    """)
    
    processing_details = textwrap.dedent("""vcf:
       chromosomes: ['foo', 'bar']
       region_length: 8
    """)
    study = vcf_study(
        root_path,
        "partitoned_vcf", ped_path, [vcf_path],
        gpf_instance, partition_description=partition_def, 
        processing_details=processing_details)
    return study

@pytest.mark.parametrize(
    "family_ids,count",
    [
        (None, 5),
        (set(["f1"]), 5)
    ],
)
def test_query_family_id(family_ids, count, imported_study):
    vs = imported_study.query_variants(family_ids=family_ids)
    vs = list(vs)
    assert len(vs) == count


@pytest.mark.parametrize(
    "person_ids,count",
    [
        (None, 5),
        (set(["m1"]), 2),
        (set(["d1"]), 3),
        (set(["p1"]), 4),
        (set(["s1"]), 2),
    ],
)
def test_query_person_id(
        person_ids, count, imported_study):
    vs = imported_study.query_variants(person_ids=person_ids)
    vs = list(vs)
    assert len(vs) == count


@pytest.mark.parametrize(
    "region,count",
    [
        (Region("foo", 1, 20), 2),
        (Region("bar", 1, 20), 3)
    ],
)
def test_query_region(region, count, imported_study):
    vs = imported_study.query_variants(regions=[region])
    vs = list(vs)
    assert len(vs) == count
