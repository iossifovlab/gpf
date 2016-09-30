'''
Created on Sep 29, 2016

@author: lubo
'''
from enrichment.config import EnrichmentResult, PHENOTYPES
from DAE import vDB
import itertools


class DenovoStudies(object):

    def __init__(self):
        self.studies = vDB.get_studies('ALL WHOLE EXOME')

    def get_studies(self, phenotype):
        assert phenotype in PHENOTYPES
        if phenotype == 'unaffected':
            studies = [st for st in self.studies
                       if 'WE' == st.get_attr('study.type')]
            return studies
        else:
            studies = []
            for st in self.studies:
                if phenotype == st.get_attr('study.phenotype') and \
                        'WE' == st.get_attr('study.type'):
                    studies.append(st)
            return studies


class Counter(EnrichmentResult):

    def __init__(self, phenotype, effect_type):
        super(Counter, self).__init__(phenotype, effect_type)
        if phenotype == 'unaffected':
            self.in_child = 'sib'
        else:
            self.in_child = 'prb'

    def count(self, studies):
        pass

    def get_variants(self, denovo_studies):
        studies = denovo_studies.get_studies(self.phenotype)
        variants = []
        for st in studies:
            vs = st.get_denovo_variants(
                inChild=self.in_child, effectTypes=self.effect_type)
            variants.append(vs)

        return itertools.chain(variants)
