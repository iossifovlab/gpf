'''
Created on Jul 27, 2015

@author: lubo
'''
from api.common.effect_types import EFFECT_GROUPS


class ReportBase(object):

    @staticmethod
    def effect_types():
        et = []
        et.extend(EFFECT_GROUPS['coding'])
        et.extend(EFFECT_GROUPS['noncoding'])
        et.extend(EFFECT_GROUPS['cnv'])

        return et

    @staticmethod
    def effect_groups():
        return ['LGDs', 'nonsynonymous', 'UTRs']


class FamilyReport(ReportBase):
    pass
