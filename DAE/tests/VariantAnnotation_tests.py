import unittest
import VariantAnnotation
from DAE import genomesDB


class VariantAnnotationTest(unittest.TestCase):

    def test_chr1_897349_sub(self):
        GA = genomesDB.get_genome()
        gmDB = genomesDB.get_gene_models()
        [effect] = VariantAnnotation.annotate_variant(gmDB, GA,
                                                      loc="1:897349",
                                                      var="sub(G->A)")
        self.assertEqual(effect.gene, "KLHL17")
        self.assertEqual(effect.transcript_id, "NM_198317_1")
        self.assertEqual(effect.strand, "+")
        self.assertEqual(effect.effect, "synonymous")
        self.assertEqual(effect.prot_pos, 211)
        self.assertEqual(effect.prot_length, 642)
        self.assertEqual(effect.aa_change, "Lys->Lys")


if __name__ == "__main__":
    unittest.main()
