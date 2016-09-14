'''
Created on Sep 14, 2016

@author: lubo
'''


def calc_race(race1, race2):
    if race1 == race2:
        return race1
    if race1 is None or race2 is None:
        return 'not-specified'
    if race1 == 'not-specified' or race2 == 'not-specified':
        return 'not-specified'

    return 'more-than-one-race'


def role_type(role_id):
    if role_id == 'mo':
        return 'mom'
    elif role_id == 'fa':
        return 'dad'
    elif role_id[0] == 'p':
        return 'prb'
    elif role_id[0] == 's' or role_id[0] == 'x':
        return 'sib'
