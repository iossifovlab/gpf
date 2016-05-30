'''
Created on Feb 29, 2016

@author: lubo
'''
from families.pheno_query import prepare_pheno_measure_query,\
    prepare_base_pheno_measure_query
from families.gender_query import prepare_family_prb_gender_query,\
    prepare_family_sib_gender_query
from families.trios_quad_query import prepare_family_trio_quad_query
from families.race_query import prepare_family_race_query
from families.study_type_query import prepare_family_study_type


def parse_family_ids(data):
    if 'familyIds' in data:
        family_ids = data['familyIds']
        del data['familyIds']

        if isinstance(family_ids, list):
            family_ids = ','.join(family_ids)
        family_ids = family_ids.strip()
        if family_ids != '':
            family_ids = set(family_ids.split(','))
            if len(family_ids) > 0:
                return family_ids
    return None


def prepare_family_query(data):
    family_ids = parse_family_ids(data)

    family_ids = prepare_base_pheno_measure_query(data, family_ids)
    assert family_ids is None or isinstance(family_ids, set)

    family_ids = prepare_pheno_measure_query(data, family_ids)
    assert family_ids is None or isinstance(family_ids, set)

    family_ids = prepare_family_prb_gender_query(data, family_ids)
    assert family_ids is None or isinstance(family_ids, set)

    family_ids = prepare_family_sib_gender_query(data, family_ids)
    assert family_ids is None or isinstance(family_ids, set)

    study_type = prepare_family_study_type(data)
    family_ids = prepare_family_trio_quad_query(data, study_type, family_ids)
    assert family_ids is None or isinstance(family_ids, set)

    family_ids = prepare_family_race_query(data, family_ids)
    assert family_ids is None or isinstance(family_ids, set)

    if family_ids is not None:
        data['familyIds'] = ",".join(family_ids)
    return study_type, data
