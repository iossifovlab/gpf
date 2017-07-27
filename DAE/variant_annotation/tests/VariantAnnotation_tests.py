import unittest
from variant_annotation.annotator import VariantAnnotator
from DAE import genomesDB
import pytest


@pytest.fixture(scope="class")
def genomes_DB(request):
    request.cls.GA = genomesDB.get_genome()
    request.cls.gmDB = genomesDB.get_gene_models()


@pytest.mark.usefixtures("genomes_DB")
class VariantAnnotationTest(unittest.TestCase):
    def test_synonymous_complex_var(self):
        [effect] = VariantAnnotator.annotate_variant(self.gmDB, self.GA,
                                                     loc="1:897349",
                                                     var="complex(GG->AA)")
        self.assertEqual(effect.gene, "KLHL17")
        self.assertEqual(effect.transcript_id, "NM_198317_1")
        self.assertEqual(effect.strand, "+")
        self.assertEqual(effect.effect, "missense")
        # self.assertEqual(effect.prot_pos, 211)
        # self.assertEqual(effect.prot_length, 642)
        self.assertEqual(effect.aa_change, "Lys,Ala->Lys,Thr")

    def test_just_next_to_splice_site_var(self):
        effects = VariantAnnotator.annotate_variant(self.gmDB, self.GA,
                                                    loc="5:86705101",
                                                    var="del(4)")
        self.assertEqual(len(effects), 2)
        effects_sorted = sorted(effects, key=lambda k: k.transcript_id)

        self.assertEqual(effects_sorted[0].gene, "CCNH")
        self.assertEqual(effects_sorted[0].transcript_id, "NM_001199189_1")
        self.assertEqual(effects_sorted[0].strand, "-")
        self.assertEqual(effects_sorted[0].effect, "intron")
        # self.assertEqual(effects_sorted[0].prot_pos, None)
        # self.assertEqual(effects_sorted[0].prot_length, None)
        self.assertEqual(effects_sorted[0].aa_change, None)

        self.assertEqual(effects_sorted[1].gene, "CCNH")
        self.assertEqual(effects_sorted[1].transcript_id, "NM_001239_1")
        self.assertEqual(effects_sorted[1].strand, "-")
        self.assertEqual(effects_sorted[1].effect, "intron")
        # self.assertEqual(effects_sorted[1].prot_pos, None)
        # self.assertEqual(effects_sorted[1].prot_length, None)
        self.assertEqual(effects_sorted[1].aa_change, None)

    def test_chr2_32853362_ins_var(self):
        effects = VariantAnnotator.annotate_variant(self.gmDB, self.GA,
                                                    loc="6:157527729",
                                                    var="complex(CTGG->ATAG)")
        self.assertEqual(len(effects), 2)
        effects_sorted = sorted(effects, key=lambda k: k.transcript_id)

        self.assertEqual(effects_sorted[0].gene, "ARID1B")
        self.assertEqual(effects_sorted[0].transcript_id, "NM_017519_1")
        self.assertEqual(effects_sorted[0].strand, "+")
        self.assertEqual(effects_sorted[0].effect, "nonsense")
        # self.assertEqual(effects_sorted[0].prot_pos, None)
        # self.assertEqual(effects_sorted[0].prot_length, None)
        self.assertEqual(effects_sorted[0].aa_change, "His,Trp->Gln,End")

        self.assertEqual(effects_sorted[1].gene, "ARID1B")
        self.assertEqual(effects_sorted[1].transcript_id, "NM_020732_1")
        self.assertEqual(effects_sorted[1].strand, "+")
        self.assertEqual(effects_sorted[1].effect, "nonsense")
        # self.assertEqual(effects_sorted[1].prot_pos, 1)
        # self.assertEqual(effects_sorted[1].prot_length, 843)
        self.assertEqual(effects_sorted[1].aa_change, "His,Trp->Gln,End")

    def test_chr5_75902128_sub_var(self):
        [effect] = VariantAnnotator.annotate_variant(self.gmDB, self.GA,
                                                     loc="5:75902128",
                                                     var="sub(C->T)")
        self.assertEqual(effect.gene, "IQGAP2")
        self.assertEqual(effect.transcript_id, "NM_006633_1")
        self.assertEqual(effect.strand, "+")
        self.assertEqual(effect.effect, "nonsense")
        # self.assertEqual(effects_sorted[0].prot_pos, None)
        # self.assertEqual(effects_sorted[0].prot_length, None)
        self.assertEqual(effect.aa_change, "Arg->End")


if __name__ == "__main__":
    unittest.main()
