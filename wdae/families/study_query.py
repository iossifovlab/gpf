'''
Created on May 30, 2016

@author: lubo
'''
from api.default_ssc_study import get_ssc_denovo_studies
from families.merge_query import merge_family_ids


def prepare_study_family_filter(data, family_ids=None):
    if 'familyStudy' not in data:
        return family_ids

    study_name = data['familyStudy']
    study = None
    for st in get_ssc_denovo_studies():
        if st.name == study_name:
            study = st
            break

    assert study is not None

    return merge_family_ids(set(study.families.keys()),
                            family_ids)
