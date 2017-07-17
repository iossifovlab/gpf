import unittest
from variant_annotation.annotator import VariantAnnotator as VariantAnnotation
from DAE import genomesDB
import pytest


@pytest.fixture(scope="class")
def genomes_DB(request):
    request.cls.GA = genomesDB.get_genome()
    request.cls.gmDB = genomesDB.get_gene_models()


@pytest.mark.usefixtures("genomes_DB")
class VariantAnnotationTest(unittest.TestCase):
    def test_chr12_130827138_del_var(self):
        effects = VariantAnnotation.annotate_variant(self.gmDB, self.GA,
                                                     loc="12:130827138",
                                                     var="del(4)")
        self.assertEqual(len(effects), 2)
        effects_sorted = sorted(effects, key=lambda k: k.transcript_id)

        self.assertEqual(effects_sorted[0].gene, "PIWIL1")
        self.assertEqual(effects_sorted[0].transcript_id, "NM_001190971_1")
        self.assertEqual(effects_sorted[0].strand, "+")
        self.assertEqual(effects_sorted[0].effect, "frame-shift")
        # self.assertEqual(effects_sorted[0].prot_pos, 1)
        # self.assertEqual(effects_sorted[0].prot_length, 830)
        self.assertEqual(effects_sorted[0].aa_change, None)

        self.assertEqual(effects_sorted[1].gene, "PIWIL1")
        self.assertEqual(effects_sorted[1].transcript_id, "NM_004764_1")
        self.assertEqual(effects_sorted[1].strand, "+")
        self.assertEqual(effects_sorted[1].effect, "frame-shift")
        # self.assertEqual(effects_sorted[1].prot_pos, 1)
        # self.assertEqual(effects_sorted[1].prot_length, 862)
        self.assertEqual(effects_sorted[1].aa_change, None)

    def test_chr12_64841908_del_var(self):
        [effect] = VariantAnnotation.annotate_variant(self.gmDB, self.GA,
                                                      loc="12:64841908",
                                                      var="del(2)")
        self.assertEqual(effect.gene, "XPOT")
        self.assertEqual(effect.transcript_id, "NM_007235_1")
        self.assertEqual(effect.strand, "+")
        self.assertEqual(effect.effect, "frame-shift")
        # self.assertEqual(effects_sorted[0].prot_pos, 962)
        # self.assertEqual(effects_sorted[0].prot_length, 962)
        self.assertEqual(effect.aa_change, None)


if __name__ == "__main__":
    unittest.main()
