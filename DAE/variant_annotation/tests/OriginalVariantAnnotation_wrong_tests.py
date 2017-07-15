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
    def test_last_codon_ins_intergenic_var(self):
        [effect] = VariantAnnotation.annotate_variant(self.gmDB, self.GA,
                                                      loc="7:24727232",
                                                      var="ins(A)")
        self.assertEqual(effect.gene, None)
        self.assertEqual(effect.transcript_id, None)
        self.assertEqual(effect.strand, None)
        self.assertEqual(effect.effect, "intergenic")
        # self.assertEqual(effect.prot_pos, None)
        # self.assertEqual(effect.prot_length, None)
        self.assertEqual(effect.aa_change, None)

    def test_no_start_var(self):
        effects = VariantAnnotation.annotate_variant(self.gmDB, self.GA,
                                                     loc="17:74729179",
                                                     var="del(3)")

        self.assertEqual(len(effects), 7)
        for effect in effects:
            self.assertEqual(effect.gene, "METTL23")
            self.assertEqual(effect.strand, "+")
            self.assertEqual(effect.aa_change, None)

        self.assertEqual(effects[0].transcript_id, "NM_001206984_1")
        self.assertEqual(effects[0].effect, "no-frame-shift")
        # self.assertEqual(effects[0].prot_pos, 68)
        # self.assertEqual(effects[0].prot_length, 190)

        self.assertEqual(effects[1].transcript_id, "NM_001206983_1")
        self.assertEqual(effects[1].effect, "no-frame-shift")
        # self.assertEqual(effects[1].prot_pos, 68)
        # self.assertEqual(effects[1].prot_length, 190)

        self.assertEqual(effects[2].transcript_id, "NM_001206985_1")
        self.assertEqual(effects[2].effect, "noStart")
        # self.assertEqual(effects[2].prot_pos, 1)
        # self.assertEqual(effects[2].prot_length, 124)

        self.assertEqual(effects[3].transcript_id, "NM_001206987_1")
        self.assertEqual(effects[3].effect, "noStart")
        # self.assertEqual(effects[3].prot_pos, 1)
        # self.assertEqual(effects[3].prot_length, 124)

        self.assertEqual(effects[4].transcript_id, "NM_001206986_1")
        self.assertEqual(effects[4].effect, "noStart")
        # self.assertEqual(effects[4].prot_pos, 1)
        # self.assertEqual(effects[4].prot_length, 124)

        self.assertEqual(effects[5].transcript_id, "NR_038193_1")
        self.assertEqual(effects[5].effect, "non-coding-intron")
        # self.assertEqual(effects[5].prot_pos, None)
        # self.assertEqual(effects[5].prot_length, None)

        self.assertEqual(effects[6].transcript_id, "NM_001080510_1")
        self.assertEqual(effects[6].effect, "no-frame-shift")
        # self.assertEqual(effects[6].prot_pos, 68)
        # self.assertEqual(effects[6].prot_length, 190)

if __name__ == "__main__":
    unittest.main()
