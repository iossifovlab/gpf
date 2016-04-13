'''
Created on Feb 29, 2016

@author: lubo
'''
import precompute


def prepare_family_study_type(data):
    if 'familyStudyType' not in data:
        return "ALL"

    study_type = data['familyStudyType']
    del data['familyStudyType']

    if study_type is None:
        return "ALL"

    families_precompute = precompute.register.get('families_precompute')
    study_type = study_type.upper()
    if study_type in families_precompute.study_types() or study_type == "ALL":
        return study_type
    return "ALL"
