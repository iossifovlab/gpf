'''
Created on Feb 29, 2016

@author: lubo
'''


def merge_family_ids(family_ids1, family_ids2):
    if family_ids1 is None:
        return family_ids2
    elif family_ids2 is None:
        return family_ids1
    else:
        return family_ids1 & family_ids2


def family_query_merge(data, family_ids):
    assert 0
    if 'familyIds' not in data:
        data['familyIds'] = ",".join(family_ids)
    else:
        family_ids = set(family_ids)
        request_family_ids = set(data['familyIds'].split(','))
        result_family_ids = family_ids & request_family_ids
        data['familyIds'] = ",".join(result_family_ids)
    return data
