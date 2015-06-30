'''
Created on Jun 22, 2015

@author: lubo
'''

from collections import defaultdict, Counter
from api.enrichment.config import PHENOTYPES
from api.enrichment.denovo_counters import filter_denovo_studies_by_phenotype

class ChildrenStats(object):
    
    @staticmethod
    def prepare_families(studies):
        fam_buff = defaultdict(dict)
        for study in studies:
            for f in study.families.values():
                for p in [f.memberInOrder[c] for c in xrange(2, len(f.memberInOrder))]:
                    if p.personId not in fam_buff[f.familyId]:
                        fam_buff[f.familyId][p.personId] = p
        return fam_buff
    
    @staticmethod
    def probands_and_siblings(studies):
        child_type_cnt = Counter()
    
        fam_buff = ChildrenStats.prepare_families(studies)
        for fmd in fam_buff.values():
            for p in fmd.values():
                child_type_cnt[p.role] += 1
    
        return dict(child_type_cnt.items())

    @staticmethod
    def probands(studies):
        child_type_cnt = Counter()
    
        fam_buff = ChildrenStats.prepare_families(studies)
        for fmd in fam_buff.values():
            for p in fmd.values():
                if p.role=='prb':
                    child_type_cnt[p.gender] += 1
    
        return dict(child_type_cnt.items())

    @staticmethod
    def siblings(studies):
        child_type_cnt = Counter()
    
        fam_buff = ChildrenStats.prepare_families(studies)
        for fmd in fam_buff.values():
            for p in fmd.values():
                if p.role=='sib':
                    child_type_cnt[p.gender] += 1
    
        return dict(child_type_cnt.items())


    @staticmethod
    def build(dsts):
        res = {}
        for phenotype in PHENOTYPES:
            if phenotype != 'unaffected':
                studies = filter_denovo_studies_by_phenotype(dsts, phenotype)
                stats = ChildrenStats.probands(studies)
                res[phenotype] = stats
            else:
                studies = [st for st in dsts if st.get_attr('study.type') == 'WE']
                stats = ChildrenStats.siblings(studies)
                res[phenotype] = stats
        
        return res