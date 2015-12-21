'''
Created on Jun 9, 2015

@author: lubo
'''
import unittest
from DAE import vDB, get_gene_sets_symNS
from api.enrichment.denovo_counters import collect_denovo_variants,\
    filter_denovo_one_event_per_family, filter_denovo_studies_by_phenotype,\
    count_denovo_variant_events
from api.enrichment.config import PRB_TESTS_SPECS, SIB_TESTS_SPECS


class DenovoCountersTest(unittest.TestCase):
    TEST_SPEC = {
        'label': 'prb|LGDs|prb|male,female|Nonsense,Frame-shift,Splice-site',
        'inchild': 'prb',
        'effect': 'LGDs'
    }

    def setUp(self):
        self.dsts = vDB.get_studies('ALL WHOLE EXOME')
        gt = get_gene_sets_symNS('main')
        self.gene_syms = gt.t2G['FMR1-targets-1006genes'].keys()

    def tearDown(self):
        pass

    def test_collect_denovo_variants(self):
        dsts = filter_denovo_studies_by_phenotype(self.dsts, 'autism')
        vs = collect_denovo_variants(dsts,
                                     **self.TEST_SPEC)
        res = filter_denovo_one_event_per_family(vs)
        self.assertEquals(606, len(res))

        count = count_denovo_variant_events(res, self.gene_syms)
        self.assertEquals(134, count)

    def test_count_denovo_variant_events_zero(self):
        count = count_denovo_variant_events([], self.gene_syms)
        self.assertEquals(0, count)

    def test_specs(self):
        dsts = filter_denovo_studies_by_phenotype(self.dsts, 'autism')

        for spec in PRB_TESTS_SPECS:
            vs = collect_denovo_variants(dsts, **spec)
            affected_gene_syms = filter_denovo_one_event_per_family(vs)
            _count = count_denovo_variant_events(
                affected_gene_syms, self.gene_syms)

        dsts = self.dsts
        for spec in SIB_TESTS_SPECS:
            vs = collect_denovo_variants(dsts, **spec)
            affected_gene_syms = filter_denovo_one_event_per_family(vs)
            _count = count_denovo_variant_events(
                affected_gene_syms, self.gene_syms)


if __name__ == "__main__":
    unittest.main()
