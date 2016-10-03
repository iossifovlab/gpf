'''
Created on Sep 30, 2016

@author: lubo
'''
import unittest

from enrichment.counters import DenovoStudies, GeneEventsCounter
from DAE import get_gene_sets_symNS
from enrichment.enrichment_builder import EnrichmentBuilder
import precompute
from enrichment.config import PHENOTYPES, EFFECT_TYPES


class EnrichmentBuilderTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        super(EnrichmentBuilderTest, cls).setUpClass()
        cls.denovo_studies = DenovoStudies()
        gt = get_gene_sets_symNS('main')
        cls.gene_set = gt.t2G['ChromatinModifiers'].keys()
        cls.background = precompute.register.get('synonymousBackgroundModel')

    def test_enrichment_builder_autism_phenotype(self):

        builder = EnrichmentBuilder(
            self.background,
            GeneEventsCounter,
            self.denovo_studies,
            self.gene_set)

        res = builder.build_phenotype('autism')

        self.assertIsNotNone(res)

        self.assertIsNotNone(res.LGDs)
        self.assertIsNotNone(res.Missense)
        self.assertIsNotNone(res.Synonymous)

        self.assertEquals(546, res.LGDs.all.count)
        self.assertEquals(36, res.LGDs.all.overlapped_count)

        self.assertEquals(2583, res.Missense.all.count)
        self.assertEquals(95, res.Missense.all.overlapped_count)

        self.assertEquals(1117, res.Synonymous.all.count)
        self.assertEquals(35, res.Synonymous.all.overlapped_count)

        self.assertEquals(39, res.LGDs.rec.count)
        self.assertEquals(9, res.LGDs.rec.overlapped_count)

        self.assertEquals(386, res.Missense.rec.count)
        self.assertEquals(20, res.Missense.rec.overlapped_count)

        self.assertEquals(76, res.Synonymous.rec.count)
        self.assertEquals(4, res.Synonymous.rec.overlapped_count)

        self.assertEquals(458, res.LGDs.male.count)
        self.assertEquals(28, res.LGDs.male.overlapped_count)

        self.assertEquals(2206, res.Missense.male.count)
        self.assertEquals(84, res.Missense.male.overlapped_count)

        self.assertEquals(961, res.Synonymous.male.count)
        self.assertEquals(31, res.Synonymous.male.overlapped_count)

        self.assertEquals(107, res.LGDs.female.count)
        self.assertEquals(13, res.LGDs.female.overlapped_count)

        self.assertEquals(505, res.Missense.female.count)
        self.assertEquals(17, res.Missense.female.overlapped_count)

        self.assertEquals(169, res.Synonymous.female.count)
        self.assertEquals(6, res.Synonymous.female.overlapped_count)

    def test_enrichment_builder_unaffected_phenotype(self):

        builder = EnrichmentBuilder(
            self.background,
            GeneEventsCounter,
            self.denovo_studies,
            self.gene_set)

        res = builder.build_phenotype('unaffected')

        self.assertIsNotNone(res)

        self.assertIsNotNone(res.LGDs)
        self.assertIsNotNone(res.Missense)
        self.assertIsNotNone(res.Synonymous)

        self.assertEquals(220, res.LGDs.all.count)
        self.assertEquals(7, res.LGDs.all.overlapped_count)

        self.assertEquals(1354, res.Missense.all.count)
        self.assertEquals(45, res.Missense.all.overlapped_count)

        self.assertEquals(595, res.Synonymous.all.count)
        self.assertEquals(17, res.Synonymous.all.overlapped_count)

        self.assertEquals(5, res.LGDs.rec.count)
        self.assertEquals(0, res.LGDs.rec.overlapped_count)

        self.assertEquals(113, res.Missense.rec.count)
        self.assertEquals(4, res.Missense.rec.overlapped_count)

        self.assertEquals(32, res.Synonymous.rec.count)
        self.assertEquals(1, res.Synonymous.rec.overlapped_count)

        self.assertEquals(113, res.LGDs.male.count)
        self.assertEquals(3, res.LGDs.male.overlapped_count)

        self.assertEquals(638, res.Missense.male.count)
        self.assertEquals(19, res.Missense.male.overlapped_count)

        self.assertEquals(300, res.Synonymous.male.count)
        self.assertEquals(13, res.Synonymous.male.overlapped_count)

        self.assertEquals(111, res.LGDs.female.count)
        self.assertEquals(4, res.LGDs.female.overlapped_count)

        self.assertEquals(782, res.Missense.female.count)
        self.assertEquals(29, res.Missense.female.overlapped_count)

        self.assertEquals(306, res.Synonymous.female.count)
        self.assertEquals(4, res.Synonymous.female.overlapped_count)

    def test_enrichment_test(self):
        builder = EnrichmentBuilder(
            self.background,
            GeneEventsCounter,
            self.denovo_studies,
            self.gene_set)

        res = builder.build()
        for phenotype in PHENOTYPES:
            self.assertIn(phenotype, res)
            pres = res[phenotype]
            for et in EFFECT_TYPES:
                self.assertIn(et, pres)
                epres = pres[et]
                self.assertIsNotNone(epres)

                self.assertEquals(phenotype, epres.phenotype)
                self.assertEquals(et, epres.effect_type)

                self.assertIn('all', epres)
                self.assertIn('rec', epres)
                self.assertIn('male', epres)
                self.assertIn('female', epres)
