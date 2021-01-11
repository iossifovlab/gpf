from dae.pedigrees.loader import FamiliesLoader
from dae.backends.vcf.loader import VcfLoader


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
        gpf_instance_2013.genomes_db.get_genome(),
        params={"vcf_chromosomes": "1;2", },
    )
    assert variants_loader is not None

    assert len(variants_loader.vcf_loaders) == 2

    indexes = []
    for sv, fvs in variants_loader.full_variants_iterator():
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
        gpf_instance_2013.genomes_db.get_genome(),
        params={
            "vcf_chromosomes": "1;2",
            "vcf_pedigree_mode": "strict",
            "vcf_include_unknown_person_genotypes": True,
            "vcf_include_unknown_family_genotypes": True,
        },
    )

    assert variants_loader is not None

    assert len(variants_loader.vcf_loaders) == 2

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
