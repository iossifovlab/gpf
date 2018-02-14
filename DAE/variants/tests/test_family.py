'''
Created on Feb 13, 2018

@author: lubo
'''
from variants.family import Family, Families


def test_study_load(uagre_loader):

    ped_df = uagre_loader.load_pedigree()

    assert ped_df is not None

    fam = Family("AU1921", ped_df)
    assert fam is not None

    print(fam.samples)
    print(fam.alleles)

    print(fam.psamples(['AU1921101', 'AU1921311']))
    print(fam.palleles(['AU1921101', 'AU1921311']))

    families = Families()
    families.families_build(ped_df)

    assert len(families.families) == 1
    assert len(families.persons) == 9
