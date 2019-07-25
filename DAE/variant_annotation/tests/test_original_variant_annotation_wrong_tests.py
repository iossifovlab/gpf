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
    def test_chr1_120387132_del_var(self):
        [effect] = VariantAnnotation.annotate_variant(self.gmDB, self.GA,
                                                      loc="1:120387132",
                                                      var="del(71)")

        self.assertEqual(effect.gene, "NBPF7")
        self.assertEqual(effect.transcript_id, "NM_001047980_1")
        self.assertEqual(effect.strand, "-")
        self.assertEqual(effect.effect, "noStart")
        self.assertEqual(effect.prot_pos, 1)
        self.assertEqual(effect.prot_length, 421)
        self.assertEqual(effect.aa_change, None)

    def test_chr2_237172988_ins_var(self):
        [effect] = VariantAnnotation.annotate_variant(self.gmDB, self.GA,
                                                      loc="2:237172988",
                                                      var="ins(TTGTTACG)")

        self.assertEqual(effect.gene, "ASB18")
        self.assertEqual(effect.transcript_id, "NM_212556_1")
        self.assertEqual(effect.strand, "-")
        self.assertEqual(effect.effect, "noStart")
        self.assertEqual(effect.prot_pos, 1)
        self.assertEqual(effect.prot_length, 466)
        self.assertEqual(effect.aa_change, None)

    # def test_chr1_802610_867930_CNV_var(self):
    #     effects = VariantAnnotation.annotate_variant(self.gmDB, self.GA,
    #                                                  loc="1:802610-867930",
    #                                                  var="CNV+")
    #     self.assertEqual(len(effects), 3)
    #     effects_sorted = sorted(effects, key=lambda k: k.transcript_id)
    #
    #     self.assertEqual(effects_sorted[0].gene, "SAMD11")
    #     self.assertEqual(effects_sorted[0].transcript_id, "NM_152486_1")
    #     self.assertEqual(effects_sorted[0].strand, "+")
    #     self.assertEqual(effects_sorted[0].effect, "unknown")
    #     # self.assertEqual(effects_sorted[0].prot_pos, None)
    #     # self.assertEqual(effects_sorted[0].prot_length, None)
    #     self.assertEqual(effects_sorted[0].aa_change, None)
    #
    #     self.assertEqual(effects_sorted[1].gene, "LOC100130417")
    #     self.assertEqual(effects_sorted[1].transcript_id, "NR_026874_1")
    #     self.assertEqual(effects_sorted[1].strand, "-")
    #     self.assertEqual(effects_sorted[1].effect, "unknown")
    #     # self.assertEqual(effects_sorted[1].prot_pos, None)
    #     # self.assertEqual(effects_sorted[1].prot_length, None)
    #     self.assertEqual(effects_sorted[1].aa_change, None)
    #
    #     self.assertEqual(effects_sorted[2].gene, "FAM41C")
    #     self.assertEqual(effects_sorted[2].transcript_id, "NR_027055_1")
    #     self.assertEqual(effects_sorted[2].strand, "-")
    #     self.assertEqual(effects_sorted[2].effect, "unknown")
    #     # self.assertEqual(effects_sorted[2].prot_pos, None)
    #     # self.assertEqual(effects_sorted[2].prot_length, None)
    #     self.assertEqual(effects_sorted[2].aa_change, None)


if __name__ == "__main__":
    unittest.main()
