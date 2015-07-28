'''
Created on Jul 27, 2015

@author: lubo
'''
from collections import defaultdict, Counter

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


class FamiliesCounter(object):
    def __init__(self, phenotype):
        self.phenotype = phenotype
        self.children_male = 0
        self.children_female = 0

    @property
    def children_total(self):
        return self.male + self.female

    def _build_families_buffer(self, studies):
        families_buffer = defaultdict(dict)
        for st in studies:
            for f in st.families.values():
                children = [f.memberInOrder[c]
                            for c in range(2, len(f.memberInOrder))]
                for p in children:
                    if p.personId in families_buffer[f.familyId]:
                        pass
                    else:
                        families_buffer[f.familyId][p.personId] = p
        return families_buffer

    def filter_studies(self, all_studies):
        if self.phenotype == 'unaffected':
            return all_studies
        studies = [st for st in all_studies
                   if st.get_attr('study.phenotype') == self.phenotype]
        return studies

    def build_families_buffer(self, all_studies):
        studies = self.filter_studies(all_studies)
        return self._build_families_buffer(studies)

    def check_phenotype(self, person):
        if self.phenotype == 'unaffected':
            return person.role == 'sib'
        else:
            return person.role == 'prb'

    def build(self, all_studies):
        families_buffer = self.build_families_buffer(all_studies)
        children_counter = Counter()
        for family in families_buffer.values():
            for person in family.values():
                if self.check_phenotype(person):
                    children_counter[person.gender] += 1

        self.children_female = children_counter['F']
        self.children_male = children_counter['M']


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

    def _calc_child_counters(self):
        pass
