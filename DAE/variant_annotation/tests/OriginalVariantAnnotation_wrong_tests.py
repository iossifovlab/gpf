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
    def test_chr3_172538026_del_var(self):
        effects = VariantAnnotation.annotate_variant(self.gmDB, self.GA,
                                                     loc="3:172538026",
                                                     var="del(6)")
        self.assertEqual(len(effects), 3)
        effects_sorted = sorted(effects, key=lambda k: k.transcript_id)

        self.assertEqual(effects_sorted[0].gene, "ECT2")
        self.assertEqual(effects_sorted[0].transcript_id, "NM_001258315_1")
        self.assertEqual(effects_sorted[0].strand, "+")
        self.assertEqual(effects_sorted[0].effect, "no-frame-shift")
        # self.assertEqual(effects_sorted[0].prot_pos, 915)
        # self.assertEqual(effects_sorted[0].prot_length, 914)
        self.assertEqual(effects_sorted[0].aa_change, None)

        self.assertEqual(effects_sorted[1].gene, "ECT2")
        self.assertEqual(effects_sorted[1].transcript_id, "NM_001258316_1")
        self.assertEqual(effects_sorted[1].strand, "+")
        self.assertEqual(effects_sorted[1].effect, "no-frame-shift")
        # self.assertEqual(effects_sorted[1].prot_pos, 884)
        # self.assertEqual(effects_sorted[1].prot_length, 883)
        self.assertEqual(effects_sorted[1].aa_change, None)

        self.assertEqual(effects_sorted[2].gene, "ECT2")
        self.assertEqual(effects_sorted[2].transcript_id, "NM_018098_1")
        self.assertEqual(effects_sorted[2].strand, "+")
        self.assertEqual(effects_sorted[2].effect, "no-frame-shift")
        # self.assertEqual(effects_sorted[2].prot_pos, 884)
        # self.assertEqual(effects_sorted[2].prot_length, 883)
        self.assertEqual(effects_sorted[2].aa_change, None)

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

    def test_chr1_11740658_ins_var(self):
        [effect] = VariantAnnotation.annotate_variant(self.gmDB, self.GA,
                                                      loc="1:11740658",
                                                      var="ins(TCCT)")

        self.assertEqual(effect.gene, None)
        self.assertEqual(effect.transcript_id, None)
        self.assertEqual(effect.strand, None)
        self.assertEqual(effect.effect, "intergenic")
        # self.assertEqual(effect.prot_pos, None)
        # self.assertEqual(effect.prot_length, None)
        self.assertEqual(effect.aa_change, None)

        def test_chr10_104629323_del_var(self):
            effects = VariantAnnotation.annotate_variant(self.gmDB, self.GA,
                                                         loc="10:104629323",
                                                         var="del(29)")
            self.assertEqual(len(effects), 2)
            effects_sorted = sorted(effects, key=lambda k: k.transcript_id)

            self.assertEqual(effects_sorted[0].gene, "AS3MT")
            self.assertEqual(effects_sorted[0].transcript_id, "NM_020682_1")
            self.assertEqual(effects_sorted[0].strand, "+")
            self.assertEqual(effects_sorted[0].effect, "frame-shift")
            # self.assertEqual(effects_sorted[0].prot_pos, 1)
            # self.assertEqual(effects_sorted[0].prot_length, 375)
            self.assertEqual(effects_sorted[0].aa_change, None)

            self.assertEqual(effects_sorted[1].gene, "C10orf32-AS3MT")
            self.assertEqual(effects_sorted[1].transcript_id, "NR_037644_1")
            self.assertEqual(effects_sorted[1].strand, "+")
            self.assertEqual(effects_sorted[1].effect, "non-coding-intron")
            # self.assertEqual(effects_sorted[1].prot_pos, None)
            # self.assertEqual(effects_sorted[1].prot_length, None)
            self.assertEqual(effects_sorted[1].aa_change, None)

        def test_chr11_123847404_ins_var(self):
            [effect] = VariantAnnotation.annotate_variant(self.gmDB, self.GA,
                                                          loc="11:123847404",
                                                          var="ins(T)")

            self.assertEqual(effect.gene, "OR10S1")
            self.assertEqual(effect.transcript_id, "NM_001004474_1")
            self.assertEqual(effect.strand, "-")
            self.assertEqual(effect.effect, "3'UTR")
            # self.assertEqual(effect.prot_pos, None)
            # self.assertEqual(effect.prot_length, None)
            self.assertEqual(effect.aa_change, None)

        def test_chr11_62931298_ins_var(self):
            [effect] = VariantAnnotation.annotate_variant(self.gmDB, self.GA,
                                                          loc="11:62931298",
                                                          var="ins(C)")

            self.assertEqual(effect.gene, "SLC22A25")
            self.assertEqual(effect.transcript_id, "NM_199352_1")
            self.assertEqual(effect.strand, "-")
            self.assertEqual(effect.effect, "3'UTR")
            # self.assertEqual(effect.prot_pos, None)
            # self.assertEqual(effect.prot_length, None)
            self.assertEqual(effect.aa_change, None)

        def test_chr12_125396262_ins_var(self):
            [effect] = VariantAnnotation.annotate_variant(self.gmDB, self.GA,
                                                          loc="12:125396262",
                                                          var="ins(T)")

            self.assertEqual(effect.gene, None)
            self.assertEqual(effect.transcript_id, None)
            self.assertEqual(effect.strand, None)
            self.assertEqual(effect.effect, "intergenic")
            # self.assertEqual(effect.prot_pos, None)
            # self.assertEqual(effect.prot_length, None)
            self.assertEqual(effect.aa_change, None)

        def test_chr16_3070391_del_var(self):
            [effect] = VariantAnnotation.annotate_variant(self.gmDB, self.GA,
                                                          loc="16:3070391",
                                                          var="del(13)")

            self.assertEqual(effect.gene, "TNFRSF12A")
            self.assertEqual(effect.transcript_id, "NM_016639_1")
            self.assertEqual(effect.strand, "+")
            self.assertEqual(effect.effect, "frame-shift")
            # self.assertEqual(effect.prot_pos, 1)
            # self.assertEqual(effect.prot_length, 129)
            self.assertEqual(effect.aa_change, None)

        def test_chr19_35249941_ins_var(self):
            [effect] = VariantAnnotation.annotate_variant(self.gmDB, self.GA,
                                                          loc="19:35249941",
                                                          var="ins(AA)")

            self.assertEqual(effect.gene, "ZNF599")
            self.assertEqual(effect.transcript_id, "NM_001007248_1")
            self.assertEqual(effect.strand, "-")
            self.assertEqual(effect.effect, "frame-shift")
            # self.assertEqual(effect.prot_pos, 589)
            # self.assertEqual(effect.prot_length, 588)
            self.assertEqual(effect.aa_change, None)

        def test_chr1_115316880_del_var(self):
            effects = VariantAnnotation.annotate_variant(self.gmDB, self.GA,
                                                         loc="1:115316880",
                                                         var="del(18)")
            self.assertEqual(len(effects), 4)
            effects_sorted = sorted(effects, key=lambda k: k.transcript_id)

            self.assertEqual(effects_sorted[0].gene, "SIKE1")
            self.assertEqual(effects_sorted[0].transcript_id, "NM_001102396_1")
            self.assertEqual(effects_sorted[0].strand, "-")
            self.assertEqual(effects_sorted[0].effect, "no-frame-shift")
            # self.assertEqual(effects_sorted[0].prot_pos, 211)
            # self.assertEqual(effects_sorted[0].prot_length, 211)
            self.assertEqual(effects_sorted[0].aa_change, None)

            self.assertEqual(effects_sorted[1].gene, "SIKE1")
            self.assertEqual(effects_sorted[1].transcript_id, "NM_025073_1")
            self.assertEqual(effects_sorted[1].strand, "-")
            self.assertEqual(effects_sorted[1].effect, "no-frame-shift")
            # self.assertEqual(effects_sorted[1].prot_pos, 207)
            # self.assertEqual(effects_sorted[1].prot_length, 207)
            self.assertEqual(effects_sorted[1].aa_change, None)

            self.assertEqual(effects_sorted[2].gene, "SIKE1")
            self.assertEqual(effects_sorted[2].transcript_id, "NR_049741_1")
            self.assertEqual(effects_sorted[2].strand, "-")
            self.assertEqual(effects_sorted[2].effect, "non-coding")
            # self.assertEqual(effects_sorted[2].prot_pos, None)
            # self.assertEqual(effects_sorted[2].prot_length, None)
            self.assertEqual(effects_sorted[2].aa_change, None)

            self.assertEqual(effects_sorted[3].gene, "SIKE1")
            self.assertEqual(effects_sorted[3].transcript_id, "NR_049742_1")
            self.assertEqual(effects_sorted[3].strand, "-")
            self.assertEqual(effects_sorted[3].effect, "non-coding")
            # self.assertEqual(effects_sorted[3].prot_pos, None)
            # self.assertEqual(effects_sorted[3].prot_length, None)
            self.assertEqual(effects_sorted[3].aa_change, None)


if __name__ == "__main__":
    unittest.main()
