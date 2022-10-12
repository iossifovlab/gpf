# pylint: disable=W0621,C0114,C0116,W0212,W0613

import pytest

from dae.testing import setup_vcf, setup_pedigree, vcf_study
from dae.utils.regions import Region


@pytest.fixture(scope="module")
def f1_vcf(tmp_path_factory):
    root_path = tmp_path_factory.mktemp("vcf_path")
    vcf_path = setup_vcf(
        root_path / "vcf_data" / "in.vcf.gz",
        """
##fileformat=VCFv4.2
##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">
##INFO=<ID=EFF,Number=1,Type=String,Description="Effect">
##INFO=<ID=INH,Number=1,Type=String,Description="Inheritance">
##contig=<ID=1>
#CHROM POS ID REF ALT QUAL FILTER INFO                   FORMAT m1  d1  c1  c2
foo    10  .  C   T,A .    .      EFF=SYN!MIS;INH=MIX    GT     0/0 0/1 0/1 0/2
foo    11  .  C   T,A .    .      EFF=SYN!MIS;INH=UKN    GT     ./. ./. ./. ./.
foo    12  .  G   A,T .    .      EFF=SYN!MIS;INH=MIX    GT     0/0 0/0 ./. 0/0
foo    13  .  C   T,A .    .      EFF=SYN!MIS;INH=DEN    GT     0/0 0/0 0/1 0/0
foo    14  .  A   G,T .    .      EFF=SYN!MIS;INH=OMI    GT     1/1 0/0 0/1 0/0
foo    15  .  G   A,T .    .      EFF=SYN!MIS;INH=MIX    GT     1/0 0/0 0/. 0/2
foo    16  .  T   C,A .    .      EFF=SYN!MIS;INH=OMI    GT     1/1 2/2 1/1 2/2
        """)

    ped_path = setup_pedigree(
        root_path / "vcf_data" / "in.ped",
        """
familyId personId dadId momId sex  status role
f1       m1       0     0     2    1      mom
f1       d1       0     0     1    1      dad
f1       c1       d1    m1    2    2      prb
f1       c2       d1    m1    1    1      sib
        """)
    return (ped_path, vcf_path)


@pytest.fixture(scope="module")
def imported_study(tmp_path_factory, f1_vcf, genotype_storage):
    # pylint: disable=import-outside-toplevel
    from ...foobar_import import foobar_gpf

    root_path = tmp_path_factory.mktemp(genotype_storage.storage_id)
    gpf_instance = foobar_gpf(root_path, genotype_storage)
    ped_path, vcf_path = f1_vcf

    return vcf_study(
        root_path, "f1_case", ped_path, [vcf_path], gpf_instance)


def test_f1_check_all_variants_effects(imported_study):
    vs = imported_study.query_variants(
        return_reference=True, return_unknown=True)
    vs = sorted(vs, key=lambda v: v.position)
    assert len(vs) == 4

    exp_num_fam_alleles = [3, 2, 2, 3]
    exp_effect_types = [
        ["synonymous", "missense"],  # pos 10
        ["noEnd"],  # pos 13
        ["intergenic"],  # pos 14
        ["intergenic", "intergenic"],  # pos 16
    ]
    for i, v in enumerate(vs):
        family_alleles = v.alleles
        assert len(family_alleles) == exp_num_fam_alleles[i]

        worst_effect_types = [fa.effects.worst for fa in family_alleles[1:]]
        assert worst_effect_types == exp_effect_types[i]


@pytest.mark.parametrize(
    "regions,inheritance,effect_types,count",
    [
        ([Region("foo", 10, 10)], None, None, 1),
        ([Region("foo", 10, 10)], "denovo", ["synonymous"], 0),
        ([Region("foo", 10, 10)], "denovo", ["missense"], 1),
        ([Region("foo", 10, 10)], "mendelian", ["synonymous"], 1),
        ([Region("foo", 10, 10)], "mendelian", ["missense"], 0),

        ([Region("foo", 11, 11)], None, None, 0),

        ([Region("foo", 12, 12)], None, None, 0),

        ([Region("foo", 13, 13)], None, None, 1),
        ([Region("foo", 13, 13)], "unknown", None, 1),
        # We check only the alt allele since return_reference=False.
        # For the alternative allele the inheritance is 'denovo'.
        # Hence this variant didn't pass.
        ([Region("foo", 13, 13)], "mendelian", None, 0),
        ([Region("foo", 13, 13)], "mendelian", ["synonymous"], 0),
        ([Region("foo", 13, 13)], None, ["noEnd"], 1),
        ([Region("foo", 13, 13)], None, ["missense"], 0),
        # We check only the alternative allele since 'return_reference=False.
        # For the alternative allele the inheritance is 'denovo'.
        # Hence this variant didn't pass.
        ([Region("foo", 13, 13)], "not denovo", None, 0),
    ],
)
def test_f1_simple(imported_study, regions, inheritance, effect_types, count):
    vs = imported_study.query_variants(
        regions=regions,
        inheritance=inheritance,
        effect_types=effect_types)
    vs = list(vs)
    assert len(vs) == count
