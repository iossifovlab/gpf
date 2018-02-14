'''
Created on Feb 7, 2018

@author: lubo
'''
import numpy as np


def test_wrapper_simple(uagre_loader):
    ped_df = uagre_loader.load_pedigree()
    vcf = uagre_loader.load_vcf()

    samples = vcf.vcf.samples
    print(samples)
    print(ped_df.personId)
    assert len(samples) == len(ped_df)

    assert np.all(ped_df.personId.values == np.array(samples))
