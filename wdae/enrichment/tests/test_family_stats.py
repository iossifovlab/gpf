'''
Created on Oct 4, 2016

@author: lubo
'''
import unittest
from enrichment.counters import DenovoStudies
from DAE import get_gene_sets_symNS
from collections import Counter
from enrichment.families import ChildrenStats


class FamilyStatsTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        super(FamilyStatsTest, cls).setUpClass()
        cls.denovo_studies = DenovoStudies()
        gt = get_gene_sets_symNS('main')
        cls.gene_set = gt.t2G['ChromatinModifiers'].keys()

    def test_count_unaffected(self):
        seen = set()
        counter = Counter()
        studies = self.denovo_studies.get_studies('unaffected')
        print([st.name for st in studies])
        for st in studies:
            for fid, fam in st.families.items():
                for p in fam.memberInOrder[2:]:
                    iid = "{}:{}".format(fid, p.personId)
                    if iid in seen:
                        continue
                    if p.role != 'sib':
                        continue

                    counter[p.gender] += 1
                    seen.add(iid)
        print(counter)

        self.assertTrue(counter['M'] > 0)
        self.assertTrue(counter['F'] > 0)
        self.assertEquals(2303, counter['F'] + counter['M'])

        stats = ChildrenStats.count(studies, 'sib')
        print(stats)

        res = ChildrenStats.build(self.denovo_studies)
        print(res)
        self.assertEquals(res['unaffected'], counter)
