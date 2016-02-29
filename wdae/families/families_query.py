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
    if 'familyIds' in data:
        family_ids = set(data['familyIds'].split(','))
    else:
        family_ids = None

    family_ids = prepare_pheno_measure_query(data, family_ids)
    assert family_ids is None or isinstance(family_ids, set)

    family_ids = prepare_family_prb_gender_query(data, family_ids)
    assert family_ids is None or isinstance(family_ids, set)

    family_ids = prepare_family_sib_gender_query(data, family_ids)
    assert family_ids is None or isinstance(family_ids, set)

    family_ids = prepare_family_trio_quad_query(data, family_ids)
    assert family_ids is None or isinstance(family_ids, set)

    family_ids = prepare_family_race_query(data, family_ids)
    assert family_ids is None or isinstance(family_ids, set)

    data['familyIds'] = ",".join(family_ids)
    return data
