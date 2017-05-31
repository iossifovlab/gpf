import unittest
import VariantAnnotation
from DAE import genomesDB
import pytest


@pytest.fixture(scope="class")
def genomes_DB(request):
    request.cls.GA = genomesDB.get_genome()
    request.cls.gmDB = genomesDB.get_gene_models()


@pytest.mark.usefixtures("genomes_DB")
class VariantAnnotationTest(unittest.TestCase):
    def assert_chr1_897349_sub(self, effect):
        self.assertEqual(effect.gene, "KLHL17")
        self.assertEqual(effect.transcript_id, "NM_198317_1")
        self.assertEqual(effect.strand, "+")
        self.assertEqual(effect.effect, "synonymous")
        self.assertEqual(effect.prot_pos, 211)
        self.assertEqual(effect.prot_length, 642)
        self.assertEqual(effect.aa_change, "Lys->Lys")

    def test_chr1_897349_sub_var(self):
        [effect] = VariantAnnotation.annotate_variant(self.gmDB, self.GA,
                                                      loc="1:897349",
                                                      var="sub(G->A)")
        self.assert_chr1_897349_sub(effect)

    def test_chr1_897349_sub_ref_alt(self):
        [effect] = VariantAnnotation.annotate_variant(self.gmDB, self.GA,
                                                      loc="1:897349",
                                                      ref="G",
                                                      alt="A")
        self.assert_chr1_897349_sub(effect)

    def test_chr1_897349_sub_ref_alt_pos(self):
        [effect] = VariantAnnotation.annotate_variant(self.gmDB, self.GA,
                                                      chr="1",
                                                      position="897349",
                                                      ref="G",
                                                      alt="A")
        self.assert_chr1_897349_sub(effect)

    def test_chr1_3519050_del_var(self):
        [effect] = VariantAnnotation.annotate_variant(self.gmDB, self.GA,
                                                      loc="1:3519050",
                                                      var="del(1)")
        self.assertEqual(effect.gene, "MEGF6")
        self.assertEqual(effect.transcript_id, "NM_001409_1")
        self.assertEqual(effect.strand, "-")
        self.assertEqual(effect.effect, "frame-shift")
        self.assertEqual(effect.prot_pos, 82)
        self.assertEqual(effect.prot_length, 1541)
        self.assertEqual(effect.aa_change, None)

    def test_chr1_53287094_ins_var(self):
        [effect] = VariantAnnotation.annotate_variant(self.gmDB, self.GA,
                                                      loc="1:53287094",
                                                      var="ins(G)")
        self.assertEqual(effect.gene, "ZYG11B")
        self.assertEqual(effect.transcript_id, "NM_024646_1")
        self.assertEqual(effect.strand, "+")
        self.assertEqual(effect.effect, "intron")
        self.assertEqual(effect.prot_pos, 682)
        self.assertEqual(effect.prot_length, 745)
        self.assertEqual(effect.aa_change, None)

    def test_chr2_238617257_ins_var(self):
        effects = VariantAnnotation.annotate_variant(self.gmDB, self.GA,
                                                     loc="2:238617257",
                                                     var="ins(A)")
        self.assertEqual(len(effects), 5)

        self.assertEqual(effects[0].gene, "LRRFIP1")
        self.assertEqual(effects[0].transcript_id, "NM_001137553_1")
        self.assertEqual(effects[0].strand, "+")
        self.assertEqual(effects[0].effect, "frame-shift")
        self.assertEqual(effects[0].prot_pos, 46)
        self.assertEqual(effects[0].prot_length, 752)
        self.assertEqual(effects[0].aa_change, None)

        self.assertEqual(effects[1].gene, "LRRFIP1")
        self.assertEqual(effects[1].transcript_id, "NM_001137552_1")
        self.assertEqual(effects[1].strand, "+")
        self.assertEqual(effects[1].effect, "frame-shift")
        self.assertEqual(effects[1].prot_pos, 46)
        self.assertEqual(effects[1].prot_length, 808)
        self.assertEqual(effects[1].aa_change, None)

        self.assertEqual(effects[2].gene, "LRRFIP1")
        self.assertEqual(effects[2].transcript_id, "NM_004735_1")
        self.assertEqual(effects[2].strand, "+")
        self.assertEqual(effects[2].effect, "frame-shift")
        self.assertEqual(effects[2].prot_pos, 46)
        self.assertEqual(effects[2].prot_length, 784)
        self.assertEqual(effects[2].aa_change, None)

        self.assertEqual(effects[3].gene, "LRRFIP1")
        self.assertEqual(effects[3].transcript_id, "NM_001137550_1")
        self.assertEqual(effects[3].strand, "+")
        self.assertEqual(effects[3].effect, "frame-shift")
        self.assertEqual(effects[3].prot_pos, 56)
        self.assertEqual(effects[3].prot_length, 640)
        self.assertEqual(effects[3].aa_change, None)

        self.assertEqual(effects[4].gene, "LRRFIP1")
        self.assertEqual(effects[4].transcript_id, "NM_001137551_1")
        self.assertEqual(effects[4].strand, "+")
        self.assertEqual(effects[4].effect, "frame-shift")
        self.assertEqual(effects[4].prot_pos, 46)
        self.assertEqual(effects[4].prot_length, 394)
        self.assertEqual(effects[4].aa_change, None)


if __name__ == "__main__":
    unittest.main()
