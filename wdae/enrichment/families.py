'''
Created on Jun 22, 2015

@author: lubo
'''

from collections import Counter

from enrichment.config import PHENOTYPES


class ChildrenStats(object):

    @staticmethod
    def count(studies, role):
        print([st.name for st in studies])
        seen = set()
        counter = Counter()
        for st in studies:
            for fid, fam in st.families.items():
                for p in fam.memberInOrder[2:]:
                    iid = "{}:{}".format(fid, p.personId)
                    if iid in seen:
                        continue
                    if p.role != role:
                        continue

                    counter[p.gender] += 1
                    seen.add(iid)
        return counter

    @staticmethod
    def build(denovo_studies):
        res = {}
        for phenotype in PHENOTYPES:
            studies = denovo_studies.get_studies(phenotype)
            if phenotype == 'unaffected':
                stats = ChildrenStats.count(studies, 'sib')
            else:
                stats = ChildrenStats.count(studies, 'prb')
            res[phenotype] = stats
        return res
