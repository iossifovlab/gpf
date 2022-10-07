# pylint: disable=W0621,C0114,C0116,W0212,W0613

from dae.pedigrees.loader import FamiliesLoader
from dae.variants_loaders.vcf.loader import VcfLoader


def test_wild_vcf_loader_simple(
        fixture_dirname, gpf_instance_2013):

    vcf_file1 = fixture_dirname("multi_vcf/multivcf_missing1_chr[vc].vcf.gz")
    vcf_file2 = fixture_dirname("multi_vcf/multivcf_missing2_chr[vc].vcf.gz")
    ped_file = fixture_dirname("multi_vcf/multivcf.ped")

    families_loader = FamiliesLoader(ped_file)
    families = families_loader.load()

    variants_loader = VcfLoader(
        families,
        [vcf_file1, vcf_file2],
        gpf_instance_2013.reference_genome,
        params={"vcf_chromosomes": "1;2", },
    )
    assert variants_loader is not None

    assert len(variants_loader.vcf_loaders) == 2

    indexes = []
    for sv, _fvs in variants_loader.full_variants_iterator():
        indexes.append(sv.summary_index)

    assert indexes == list(range(len(indexes)))


def test_wild_vcf_loader_pedigree(
        fixture_dirname, gpf_instance_2013):

    vcf_file1 = fixture_dirname("multi_vcf/multivcf_pedigree1_chr[vc].vcf.gz")
    vcf_file2 = fixture_dirname("multi_vcf/multivcf_pedigree2_chr[vc].vcf.gz")
    ped_file = fixture_dirname("multi_vcf/multivcf.ped")

    families_loader = FamiliesLoader(ped_file)
    families = families_loader.load()

    variants_loader = VcfLoader(
        families,
        [vcf_file1, vcf_file2],
        gpf_instance_2013.reference_genome,
        params={
            "vcf_chromosomes": "1;2",
            "vcf_pedigree_mode": "fixed",
            "vcf_include_unknown_person_genotypes": True,
            "vcf_include_unknown_family_genotypes": True,
        },
    )

    assert variants_loader is not None

    assert len(variants_loader.vcf_loaders) == 2
    for vcf_loader in variants_loader.vcf_loaders:
        assert vcf_loader.fixed_pedigree

    indexes = []
    for sv, fvs in variants_loader.full_variants_iterator():
        indexes.append(sv.summary_index)
        for fv in fvs:
            print(fv)

    assert indexes == list(range(len(indexes)))

    for vcf_loader in variants_loader.vcf_loaders:
        print(vcf_loader.families.persons)

    families1 = variants_loader.vcf_loaders[0].families
    families2 = variants_loader.vcf_loaders[1].families

    for p1, p2 in zip(families1.persons.values(), families2.persons.values()):
        assert p1 == p2

    for fid in families1.keys():

        f1 = families1[fid]
        f2 = families2[fid]
        assert f1 == f2


def test_wild_vcf_loader_pedigree_union(
        fixture_dirname, gpf_instance_2013):

    # f1: f1.mom f1.dad f1.p1 f1.s1
    # f2: f2.mom f2.dad f2.p1 f2.s1
    # f3: f3.mom f3.dad f3.p1 f3.s1
    # f4: f4.mom f4.dad f4.p1 f4.s1
    # f5: f5.mom f5.dad f5.p1 f5.s1

    vcf_file1 = fixture_dirname("multi_vcf/multivcf_pedigree1_chr[vc].vcf.gz")
    vcf_file2 = fixture_dirname("multi_vcf/multivcf_pedigree2_chr[vc].vcf.gz")
    ped_file = fixture_dirname("multi_vcf/multivcf.ped")

    families_loader = FamiliesLoader(ped_file)
    families = families_loader.load()

    variants_loader = VcfLoader(
        families,
        [vcf_file1, vcf_file2],
        gpf_instance_2013.reference_genome,
        params={
            "vcf_chromosomes": "1;2",
            "vcf_pedigree_mode": "union",
            "vcf_include_unknown_person_genotypes": True,
            "vcf_include_unknown_family_genotypes": True,
        },
    )

    assert variants_loader is not None

    assert len(variants_loader.vcf_loaders) == 2

    for vcf_loader in variants_loader.vcf_loaders:
        print(vcf_loader.families.persons)

    families = variants_loader.families
    families1 = variants_loader.vcf_loaders[0].families
    families2 = variants_loader.vcf_loaders[1].families

    for p1, p2 in zip(families1.persons.values(), families2.persons.values()):
        assert p1 == p2

    for fid in families1.keys():

        f1 = families1[fid]
        f2 = families2[fid]
        assert f1 == f2

    assert len(families.persons) == 20
    assert len(families1.persons) == 20
    assert len(families2.persons) == 20

    for person in families.persons.values():
        assert not person.missing, person
