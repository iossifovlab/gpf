'''
Created on Jul 27, 2015

@author: lubo
'''
from api.common.effect_types import EFFECT_GROUPS
from DAE import vDB


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

    def __init__(self, study_name):
        self.study_name = study_name
        self.studies = vDB.get_studies(self.study_name)

    @property
    def phenotypes(self):
        phenotypes = set([st.get_attr('study.phenotype')
                          for st in self.studies])
        phenotypes = list(phenotypes)
        phenotypes.sort()
        phenotypes.append('unaffected')
        return phenotypes
