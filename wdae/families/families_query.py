'''
Created on Feb 29, 2016

@author: lubo
'''
from families.pheno_query import prepare_pheno_measure_query
from families.gender_query import prepare_family_prb_gender_query,\
    prepare_family_sib_gender_query
from families.trios_quad_query import prepare_family_trio_quad_query
from families.race_query import prepare_family_race_query


def prepare_family_query(data):
    data = prepare_pheno_measure_query(data)
    data = prepare_family_prb_gender_query(data)
    data = prepare_family_sib_gender_query(data)
    data = prepare_family_trio_quad_query(data)
    data = prepare_family_race_query(data)
    return data
