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

    def test_chr1_95712170_del_var(self):
        effects = VariantAnnotation.annotate_variant(self.gmDB, self.GA,
                                                     loc="1:95712170",
                                                     var="del(3)")
        self.assertEqual(len(effects), 7)
        effects_sorted = sorted(effects, key=lambda k: k.transcript_id)

        self.assertEqual(effects_sorted[0].gene, "RWDD3")
        self.assertEqual(effects_sorted[0].transcript_id, "NM_001128142_1")
        self.assertEqual(effects_sorted[0].strand, "+")
        self.assertEqual(effects_sorted[0].effect, "3'UTR-intron")
        # self.assertEqual(effects_sorted[0].prot_pos, None)
        # self.assertEqual(effects_sorted[0].prot_length, None)
        self.assertEqual(effects_sorted[0].aa_change, None)

        self.assertEqual(effects_sorted[1].gene, "RWDD3")
        self.assertEqual(effects_sorted[1].transcript_id, "NM_001199682_1")
        self.assertEqual(effects_sorted[1].strand, "+")
        self.assertEqual(effects_sorted[1].effect, "no-frame-shift")
        # self.assertEqual(effects_sorted[1].prot_pos, 200)
        # self.assertEqual(effects_sorted[1].prot_length, 200)
        self.assertEqual(effects_sorted[1].aa_change, None)

        self.assertEqual(effects_sorted[2].gene, "RWDD3")
        self.assertEqual(effects_sorted[2].transcript_id, "NM_001278247_1")
        self.assertEqual(effects_sorted[2].strand, "+")
        self.assertEqual(effects_sorted[2].effect, "no-frame-shift")
        # self.assertEqual(effects_sorted[3].prot_pos, 185)
        # self.assertEqual(effects_sorted[3].prot_length, 185)
        self.assertEqual(effects_sorted[2].aa_change, None)

        self.assertEqual(effects_sorted[3].gene, "RWDD3")
        self.assertEqual(effects_sorted[3].transcript_id, "NM_001278248_1")
        self.assertEqual(effects_sorted[3].strand, "+")
        self.assertEqual(effects_sorted[3].effect, "no-frame-shift")
        # self.assertEqual(effects_sorted[5].prot_pos, 201)
        # self.assertEqual(effects_sorted[5].prot_length, 252)
        self.assertEqual(effects_sorted[3].aa_change, None)

        self.assertEqual(effects_sorted[4].gene, "RWDD3")
        self.assertEqual(effects_sorted[4].transcript_id, "NM_015485_1")
        self.assertEqual(effects_sorted[4].strand, "+")
        self.assertEqual(effects_sorted[4].effect, "no-frame-shift")
        # self.assertEqual(effects_sorted[6].prot_pos, 216)
        # self.assertEqual(effects_sorted[6].prot_length, 267)
        self.assertEqual(effects_sorted[4].aa_change, None)

        self.assertEqual(effects_sorted[5].gene, "RWDD3")
        self.assertEqual(effects_sorted[5].transcript_id, "NR_103483_1")
        self.assertEqual(effects_sorted[5].strand, "+")
        self.assertEqual(effects_sorted[5].effect, "non-coding")
        # self.assertEqual(effects_sorted[7].prot_pos, None)
        # self.assertEqual(effects_sorted[7].prot_length, None)
        self.assertEqual(effects_sorted[5].aa_change, None)

        self.assertEqual(effects_sorted[6].gene, "RWDD3")
        self.assertEqual(effects_sorted[6].transcript_id, "NR_103484_1")
        self.assertEqual(effects_sorted[6].strand, "+")
        self.assertEqual(effects_sorted[6].effect, "non-coding")
        # self.assertEqual(effects_sorted[8].prot_pos, None)
        # self.assertEqual(effects_sorted[8].prot_length, None)
        self.assertEqual(effects_sorted[6].aa_change, None)

    def test_chr19_35249941_ins_var(self):
        [effect] = VariantAnnotation.annotate_variant(self.gmDB, self.GA,
                                                      loc="19:35249941",
                                                      var="ins(AA)")

        self.assertEqual(effect.gene, "ZNF599")
        self.assertEqual(effect.transcript_id, "NM_001007248_1")
        self.assertEqual(effect.strand, "-")
        self.assertEqual(effect.effect, "noEnd")
        # self.assertEqual(effect.prot_pos, 589)
        # self.assertEqual(effect.prot_length, 588)
        self.assertEqual(effect.aa_change, None)


if __name__ == "__main__":
    unittest.main()
