'''
Created on Feb 13, 2018

@author: lubo
'''
from variants.family import Family


def test_study_load(uagre_loader):

    ped_df, _ped = uagre_loader.load_pedigree()

    assert ped_df is not None

    fam = Family("AU1921", ped_df)
    assert fam is not None

    print(fam.samples)
    print(fam.allels)

    print(fam.psamples(['AU1921101', 'AU1921311']))
    print(fam.pallels(['AU1921101', 'AU1921311']))
