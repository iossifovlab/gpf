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


if __name__ == "__main__":
    unittest.main()
