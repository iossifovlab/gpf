'''
Created on Feb 13, 2018

@author: lubo
'''
from variants.family import FamiliesBase, Family
from variants.raw_vcf import VcfFamily
import pytest


def test_load(ustudy_loader):

    ped_df = ustudy_loader.load_pedigree()

    assert ped_df is not None

    fam = Family("AU1921", ped_df)
    assert fam is not None

    with pytest.raises(AssertionError):
        VcfFamily("AU1921", ped_df)

#     print(fam.samples)
#     print(fam.alleles)
#
#     print(fam.vcf_samples_index(['AU1921101', 'AU1921311']))
#     print(fam.vcf_alleles_index(['AU1921101', 'AU1921311']))

    families = FamiliesBase()
    families.families_build(ped_df)

    assert len(families.families) == 1
    assert len(families.persons) == 9
