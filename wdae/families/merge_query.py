'''
Created on Feb 29, 2016

@author: lubo
'''


def family_query_merge(data, family_ids):
    if 'familyIds' not in data:
        data['familyIds'] = ",".join(family_ids)
    else:
        family_ids = set(family_ids)
        request_family_ids = set(data['familyIds'].split(','))
        result_family_ids = family_ids & request_family_ids
        data['familyIds'] = ",".join(result_family_ids)
    return data
