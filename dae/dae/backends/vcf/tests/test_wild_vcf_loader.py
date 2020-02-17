from dae.pedigrees.loader import FamiliesLoader
from dae.backends.vcf.loader import VcfLoader


def test_wild_vcf_loader_simple(
        fixture_dirname, gpf_instance_2013, temp_dirname):

    vcf_file1 = fixture_dirname('multi_vcf/multivcf_missing1_chr{vw}.vcf.gz')
    vcf_file2 = fixture_dirname('multi_vcf/multivcf_missing2_chr{vw}.vcf.gz')
    ped_file = fixture_dirname('multi_vcf/multivcf.ped')

    families_loader = FamiliesLoader(ped_file)
    families = families_loader.load()

    variants_loader = VcfLoader(
        families,
        [vcf_file1, vcf_file2],
        gpf_instance_2013.genomes_db.get_genome(),
        params={
            'vcf_wildcards': '1;2',
        }
    )
    assert variants_loader is not None

    assert len(variants_loader.vcf_loaders) == 2

    indexes = []
    for sv, fvs in variants_loader.full_variants_iterator():
        indexes.append(sv.summary_index)

    assert indexes == list(range(len(indexes)))
