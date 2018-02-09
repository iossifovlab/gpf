'''
Created on Feb 9, 2018

@author: lubo
'''
from variants.study import Study


def test_study_load(uagre_config):

    study = Study(uagre_config)
    study.load()

    assert study.vars_df is not None
    assert study.vcf_vars is not None

    assert len(study.vars_df) == len(study.vcf_vars)
