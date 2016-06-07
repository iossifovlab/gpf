'''
Created on May 30, 2016

@author: lubo
'''
from api.default_ssc_study import get_ssc_denovo_studies
from families.merge_query import merge_family_ids


def prepare_study_family_filter(data, study_type, family_ids=None):
    if 'familyStudies' not in data:
        return family_ids

    study_name = data['familyStudies']
    study = None
    for st in get_ssc_denovo_studies():
        if st.name == study_name:
            study = st
            break

    assert study is not None
    if study_type == 'ALL' or study_type == study.get_attr('study.type'):
        return merge_family_ids(set(study.families.keys()),
                                family_ids)
    else:
        return set()
