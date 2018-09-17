from __future__ import unicode_literals
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
    def test_reverse_strand_frame_shift_var(self):
        [effect] = VariantAnnotation.annotate_variant(self.gmDB, self.GA,
                                                      loc="1:897349",
                                                      var="complex(G->CCAA)")
        self.assertEqual(effect.gene, "KLHL17")
        self.assertEqual(effect.transcript_id, "NM_198317_1")
        self.assertEqual(effect.strand, "+")
        self.assertEqual(effect.effect, "no-frame-shift")
        self.assertEqual(effect.prot_pos, 1)
        self.assertEqual(effect.prot_length, 100)
        self.assertEqual(effect.aa_change, None)


if __name__ == "__main__":
    unittest.main()
