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
        self.assertEqual(effect.effect, "noEnd")
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
        self.assertEqual(effects_sorted[1].effect, "noEnd")
        # self.assertEqual(effects_sorted[1].prot_pos, 200)
        # self.assertEqual(effects_sorted[1].prot_length, 200)
        self.assertEqual(effects_sorted[1].aa_change, None)

        self.assertEqual(effects_sorted[2].gene, "RWDD3")
        self.assertEqual(effects_sorted[2].transcript_id, "NM_001278247_1")
        self.assertEqual(effects_sorted[2].strand, "+")
        self.assertEqual(effects_sorted[2].effect, "noEnd")
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

    def test_chr3_195966608_del_var(self):
        [effect] = VariantAnnotation.annotate_variant(self.gmDB, self.GA,
                                                      loc="3:195966608",
                                                      var="del(4)")

        self.assertEqual(effect.gene, "PCYT1A")
        self.assertEqual(effect.transcript_id, "NM_005017_1")
        self.assertEqual(effect.strand, "-")
        self.assertEqual(effect.effect, "splice-site")
        # self.assertEqual(effect.prot_pos, 237)
        # self.assertEqual(effect.prot_length, 368)
        self.assertEqual(effect.aa_change, None)

    def test_chr1_156786466_ins_var(self):
        effects = VariantAnnotation.annotate_variant(self.gmDB, self.GA,
                                                     loc="1:156786466",
                                                     var="ins(A)")
        self.assertEqual(len(effects), 5)
        effects_sorted = sorted(effects, key=lambda k: k.transcript_id)

        self.assertEqual(effects_sorted[0].gene, "NTRK1")
        self.assertEqual(effects_sorted[0].transcript_id, "NM_001007792_1")
        self.assertEqual(effects_sorted[0].strand, "+")
        self.assertEqual(effects_sorted[0].effect, "intron")
        # self.assertEqual(effects_sorted[0].prot_pos, 3)
        # self.assertEqual(effects_sorted[0].prot_length, 761)
        self.assertEqual(effects_sorted[0].aa_change, None)

        self.assertEqual(effects_sorted[1].gene, "SH2D2A")
        self.assertEqual(effects_sorted[1].transcript_id, "NM_001161441_1")
        self.assertEqual(effects_sorted[1].strand, "-")
        self.assertEqual(effects_sorted[1].effect, "splice-site")
        # self.assertEqual(effects_sorted[1].prot_pos, 12)
        # self.assertEqual(effects_sorted[1].prot_length, 400)
        self.assertEqual(effects_sorted[1].aa_change, None)

        self.assertEqual(effects_sorted[2].gene, "SH2D2A")
        self.assertEqual(effects_sorted[2].transcript_id, "NM_001161442_1")
        self.assertEqual(effects_sorted[2].strand, "-")
        self.assertEqual(effects_sorted[2].effect, "splice-site")
        # self.assertEqual(effects_sorted[2].prot_pos, 4)
        # self.assertEqual(effects_sorted[2].prot_length, 372)
        self.assertEqual(effects_sorted[2].aa_change, None)

        self.assertEqual(effects_sorted[3].gene, "SH2D2A")
        self.assertEqual(effects_sorted[3].transcript_id, "NM_001161444_1")
        self.assertEqual(effects_sorted[3].strand, "-")
        self.assertEqual(effects_sorted[3].effect, "splice-site")
        # self.assertEqual(effects_sorted[3].prot_pos, 12)
        # self.assertEqual(effects_sorted[3].prot_length, 390)
        self.assertEqual(effects_sorted[3].aa_change, None)

        self.assertEqual(effects_sorted[4].gene, "SH2D2A")
        self.assertEqual(effects_sorted[4].transcript_id, "NM_003975_1")
        self.assertEqual(effects_sorted[4].strand, "-")
        self.assertEqual(effects_sorted[4].effect, "splice-site")
        # self.assertEqual(effects_sorted[4].prot_pos, 12)
        # self.assertEqual(effects_sorted[4].prot_length, 390)
        self.assertEqual(effects_sorted[4].aa_change, None)

    def test_chr1_21050866_del_var(self):
        effects = VariantAnnotation.annotate_variant(self.gmDB, self.GA,
                                                     loc="1:21050866",
                                                     var="del(34)")
        self.assertEqual(len(effects), 2)
        effects_sorted = sorted(effects, key=lambda k: k.transcript_id)

        self.assertEqual(effects_sorted[0].gene, "SH2D5")
        self.assertEqual(effects_sorted[0].transcript_id, "NM_001103160_1")
        self.assertEqual(effects_sorted[0].strand, "-")
        self.assertEqual(effects_sorted[0].effect, "splice-site")
        # self.assertEqual(effects_sorted[0].prot_pos, 123)
        # self.assertEqual(effects_sorted[0].prot_length, 339)
        self.assertEqual(effects_sorted[0].aa_change, None)

        self.assertEqual(effects_sorted[1].gene, "SH2D5")
        self.assertEqual(effects_sorted[1].transcript_id, "NM_001103161_1")
        self.assertEqual(effects_sorted[1].strand, "-")
        self.assertEqual(effects_sorted[1].effect, "splice-site")
        # self.assertEqual(effects_sorted[1].prot_pos, 207)
        # self.assertEqual(effects_sorted[1].prot_length, 423)
        self.assertEqual(effects_sorted[1].aa_change, None)

    def test_chr2_111753543_del_var(self):
        [effect] = VariantAnnotation.annotate_variant(self.gmDB, self.GA,
                                                      loc="2:111753543",
                                                      var="del(54)")

        self.assertEqual(effect.gene, "ACOXL")
        self.assertEqual(effect.transcript_id, "NM_001142807_1")
        self.assertEqual(effect.strand, "+")
        self.assertEqual(effect.effect, "splice-site")
        # self.assertEqual(effect.prot_pos, 415)
        # self.assertEqual(effect.prot_length, 580)
        self.assertEqual(effect.aa_change, None)

    def test_chr3_97611838_del_var(self):
        [effect] = VariantAnnotation.annotate_variant(self.gmDB, self.GA,
                                                      loc="3:97611838",
                                                      var="del(4)")

        self.assertEqual(effect.gene, "CRYBG3")
        self.assertEqual(effect.transcript_id, "NM_153605_1")
        self.assertEqual(effect.strand, "+")
        self.assertEqual(effect.effect, "splice-site")
        # self.assertEqual(effect.prot_pos, 2525)
        # self.assertEqual(effect.prot_length, 2971)
        self.assertEqual(effect.aa_change, None)

    def test_chr13_21729291_ins_var(self):
        var = "ins(AGTTTTCTTTGTTGCTGACATCTC" \
            "GGATGTTCTGTCCATGTTTAAGGAACCTTTTACTGGGTGGCACTGCTTTAAT)"
        effects = VariantAnnotation.annotate_variant(self.gmDB, self.GA,
                                                     loc="13:21729291",
                                                     var=var)
        self.assertEqual(len(effects), 2)
        effects_sorted = sorted(effects, key=lambda k: k.transcript_id)

        self.assertEqual(effects_sorted[0].gene, "SKA3")
        self.assertEqual(effects_sorted[0].transcript_id, "NM_001166017_1")
        self.assertEqual(effects_sorted[0].strand, "-")
        self.assertEqual(effects_sorted[0].effect, "splice-site")
        # self.assertEqual(effects_sorted[0].prot_pos, 374)
        # self.assertEqual(effects_sorted[0].prot_length, 389)
        self.assertEqual(effects_sorted[0].aa_change, None)

        self.assertEqual(effects_sorted[1].gene, "SKA3")
        self.assertEqual(effects_sorted[1].transcript_id, "NM_145061_1")
        self.assertEqual(effects_sorted[1].strand, "-")
        self.assertEqual(effects_sorted[1].effect, "splice-site")
        # self.assertEqual(effects_sorted[1].prot_pos, 414)
        # self.assertEqual(effects_sorted[1].prot_length, 412)
        self.assertEqual(effects_sorted[1].aa_change, None)

    def test_chr12_93792633_ins_var(self):
        effects = VariantAnnotation.annotate_variant(self.gmDB, self.GA,
                                                     loc="12:93792633",
                                                     var="ins(T)")
        self.assertEqual(len(effects), 4)
        effects_sorted = sorted(effects, key=lambda k: k.transcript_id)

        self.assertEqual(effects_sorted[0].gene, "NUDT4")
        self.assertEqual(effects_sorted[0].transcript_id, "NM_019094_1")
        self.assertEqual(effects_sorted[0].strand, "+")
        self.assertEqual(effects_sorted[0].effect, "splice-site")
        # self.assertEqual(effects_sorted[0].prot_pos, 114)
        # self.assertEqual(effects_sorted[0].prot_length, 181)
        self.assertEqual(effects_sorted[0].aa_change, None)

        self.assertEqual(effects_sorted[1].gene, "NUDT4")
        self.assertEqual(effects_sorted[1].transcript_id, "NM_199040_1")
        self.assertEqual(effects_sorted[1].strand, "+")
        self.assertEqual(effects_sorted[1].effect, "splice-site")
        # self.assertEqual(effects_sorted[1].prot_pos, 115)
        # self.assertEqual(effects_sorted[1].prot_length, 182)
        self.assertEqual(effects_sorted[1].aa_change, None)

        self.assertEqual(effects_sorted[2].gene, "NUDT4P1")
        self.assertEqual(effects_sorted[2].transcript_id, "NR_002212_1")
        self.assertEqual(effects_sorted[2].strand, "+")
        self.assertEqual(effects_sorted[2].effect, "splice-site")
        # self.assertEqual(effects_sorted[2].prot_pos, None)
        # self.assertEqual(effects_sorted[2].prot_length, None)
        self.assertEqual(effects_sorted[2].aa_change, None)

        self.assertEqual(effects_sorted[3].gene, "NUDT4P2")
        self.assertEqual(effects_sorted[3].transcript_id, "NR_104005_1")
        self.assertEqual(effects_sorted[3].strand, "+")
        self.assertEqual(effects_sorted[3].effect, "splice-site")
        # self.assertEqual(effects_sorted[3].prot_pos, None)
        # self.assertEqual(effects_sorted[3].prot_length, None)
        self.assertEqual(effects_sorted[3].aa_change, None)

    def test_chr17_4086688_del_var(self):
        effects = VariantAnnotation.annotate_variant(self.gmDB, self.GA,
                                                     loc="17:4086688",
                                                     var="del(4)")
        self.assertEqual(len(effects), 3)
        effects_sorted = sorted(effects, key=lambda k: k.transcript_id)

        self.assertEqual(effects_sorted[0].gene, "ANKFY1")
        self.assertEqual(effects_sorted[0].transcript_id, "NM_001257999_1")
        self.assertEqual(effects_sorted[0].strand, "-")
        self.assertEqual(effects_sorted[0].effect, "splice-site")
        # self.assertEqual(effects_sorted[0].prot_pos, 693)
        # self.assertEqual(effects_sorted[0].prot_length, 1212)
        self.assertEqual(effects_sorted[0].aa_change, None)

        self.assertEqual(effects_sorted[1].gene, "ANKFY1")
        self.assertEqual(effects_sorted[1].transcript_id, "NM_016376_1")
        self.assertEqual(effects_sorted[1].strand, "-")
        self.assertEqual(effects_sorted[1].effect, "splice-site")
        # self.assertEqual(effects_sorted[1].prot_pos, 651)
        # self.assertEqual(effects_sorted[1].prot_length, 1171)
        self.assertEqual(effects_sorted[1].aa_change, None)

        self.assertEqual(effects_sorted[2].gene, "ANKFY1")
        self.assertEqual(effects_sorted[2].transcript_id, "NR_047571_1")
        self.assertEqual(effects_sorted[2].strand, "-")
        self.assertEqual(effects_sorted[2].effect, "splice-site")
        # self.assertEqual(effects_sorted[2].prot_pos, None)
        # self.assertEqual(effects_sorted[2].prot_length, None)
        self.assertEqual(effects_sorted[2].aa_change, None)


    def test_chr21_11049623_sub_var(self):
        effects = VariantAnnotation.annotate_variant(self.gmDB, self.GA,
                                                     loc="21:11049623",
                                                     var="sub(T->C)")
        self.assertEqual(len(effects), 4)
        effects_sorted = sorted(effects, key=lambda k: k.transcript_id)

        self.assertEqual(effects_sorted[0].gene, "BAGE4")
        self.assertEqual(effects_sorted[0].transcript_id, "NM_181704_1")
        self.assertEqual(effects_sorted[0].strand, "-")
        self.assertEqual(effects_sorted[0].effect, "splice-site")
        # self.assertEqual(effects_sorted[0].prot_pos, None)
        # self.assertEqual(effects_sorted[0].prot_length, None)
        self.assertEqual(effects_sorted[0].aa_change, None)

        self.assertEqual(effects_sorted[1].gene, "BAGE3")
        self.assertEqual(effects_sorted[1].transcript_id, "NM_182481_1")
        self.assertEqual(effects_sorted[1].strand, "-")
        self.assertEqual(effects_sorted[1].effect, "splice-site")
        # self.assertEqual(effects_sorted[1].prot_pos, 94)
        # self.assertEqual(effects_sorted[1].prot_length, 110)
        self.assertEqual(effects_sorted[1].aa_change, None)

        self.assertEqual(effects_sorted[2].gene, "BAGE2")
        self.assertEqual(effects_sorted[2].transcript_id, "NM_182482_1")
        self.assertEqual(effects_sorted[2].strand, "-")
        self.assertEqual(effects_sorted[2].effect, "splice-site")
        # self.assertEqual(effects_sorted[2].prot_pos, 94)
        # self.assertEqual(effects_sorted[2].prot_length, 110)
        self.assertEqual(effects_sorted[2].aa_change, None)

        self.assertEqual(effects_sorted[3].gene, "BAGE5")
        self.assertEqual(effects_sorted[3].transcript_id, "NM_182484_1")
        self.assertEqual(effects_sorted[3].strand, "-")
        self.assertEqual(effects_sorted[3].effect, "splice-site")
        # self.assertEqual(effects_sorted[3].prot_pos, None)
        # self.assertEqual(effects_sorted[3].prot_length, None)
        self.assertEqual(effects_sorted[3].aa_change, None)


if __name__ == "__main__":
    unittest.main()
