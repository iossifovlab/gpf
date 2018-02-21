'''
Created on Feb 13, 2018

@author: lubo
'''
from variants.family import Families
from variants.raw_vcf import VcfFamily


def test_load(uagre_loader):

    ped_df = uagre_loader.load_pedigree()

    assert ped_df is not None

    fam = VcfFamily("AU1921", ped_df)
    assert fam is not None

    print(fam.samples)
    print(fam.alleles)

    print(fam.vcf_samples_index(['AU1921101', 'AU1921311']))
    print(fam.vcf_alleles_index(['AU1921101', 'AU1921311']))

    families = Families()
    families.families_build(ped_df)

    assert len(families.families) == 1
    assert len(families.persons) == 9
