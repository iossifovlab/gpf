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
        self.assertEqual(effects_sorted[2].effect, "non-coding-intron")
        # self.assertEqual(effects_sorted[2].prot_pos, None)
        # self.assertEqual(effects_sorted[2].prot_length, None)
        self.assertEqual(effects_sorted[2].aa_change, None)

        self.assertEqual(effects_sorted[3].gene, "NUDT4P2")
        self.assertEqual(effects_sorted[3].transcript_id, "NR_104005_1")
        self.assertEqual(effects_sorted[3].strand, "+")
        self.assertEqual(effects_sorted[3].effect, "non-coding-intron")
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
        self.assertEqual(effects_sorted[2].effect, "non-coding-intron")
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

    def test_chr1_71530819_del_var(self):
        effects = VariantAnnotation.annotate_variant(self.gmDB, self.GA,
                                                     loc="1:71530819",
                                                     var="del(4)")
        self.assertEqual(len(effects), 3)
        effects_sorted = sorted(effects, key=lambda k: k.transcript_id)

        self.assertEqual(effects_sorted[0].gene, "ZRANB2")
        self.assertEqual(effects_sorted[0].transcript_id, "NM_005455_1")
        self.assertEqual(effects_sorted[0].strand, "-")
        self.assertEqual(effects_sorted[0].effect, "splice-site")
        # self.assertEqual(effects_sorted[0].prot_pos, None)
        # self.assertEqual(effects_sorted[0].prot_length, None)
        self.assertEqual(effects_sorted[0].aa_change, None)

        self.assertEqual(effects_sorted[1].gene, "ZRANB2")
        self.assertEqual(effects_sorted[1].transcript_id, "NM_203350_1")
        self.assertEqual(effects_sorted[1].strand, "-")
        self.assertEqual(effects_sorted[1].effect, "splice-site")
        # self.assertEqual(effects_sorted[1].prot_pos, 310)
        # self.assertEqual(effects_sorted[1].prot_length, 330)
        self.assertEqual(effects_sorted[1].aa_change, None)

        self.assertEqual(effects_sorted[2].gene, "ZRANB2-AS1")
        self.assertEqual(effects_sorted[2].transcript_id, "NR_038420_1")
        self.assertEqual(effects_sorted[2].strand, "+")
        self.assertEqual(effects_sorted[2].effect, "non-coding-intron")
        # self.assertEqual(effects_sorted[2].prot_pos, None)
        # self.assertEqual(effects_sorted[2].prot_length, None)
        self.assertEqual(effects_sorted[2].aa_change, None)

    def test_chr1_43917074_del_var(self):
        effects = VariantAnnotation.annotate_variant(self.gmDB, self.GA,
                                                     loc="1:43917074",
                                                     var="del(16)")
        self.assertEqual(len(effects), 4)
        effects_sorted = sorted(effects, key=lambda k: k.transcript_id)

        self.assertEqual(effects_sorted[0].gene, "HYI")
        self.assertEqual(effects_sorted[0].transcript_id, "NM_001190880_1")
        self.assertEqual(effects_sorted[0].strand, "-")
        self.assertEqual(effects_sorted[0].effect, "splice-site")
        # self.assertEqual(effects_sorted[0].prot_pos, 251)
        # self.assertEqual(effects_sorted[0].prot_length, 277)
        self.assertEqual(effects_sorted[0].aa_change, None)

        self.assertEqual(effects_sorted[1].gene, "HYI")
        self.assertEqual(effects_sorted[1].transcript_id, "NM_001243526_1")
        self.assertEqual(effects_sorted[1].strand, "-")
        self.assertEqual(effects_sorted[1].effect, "intron")
        # self.assertEqual(effects_sorted[1].prot_pos, 273)
        # self.assertEqual(effects_sorted[1].prot_length, 273)
        self.assertEqual(effects_sorted[1].aa_change, None)

        self.assertEqual(effects_sorted[2].gene, "SZT2")
        self.assertEqual(effects_sorted[2].transcript_id, "NM_015284_1")
        self.assertEqual(effects_sorted[2].strand, "+")
        self.assertEqual(effects_sorted[2].effect, "3'UTR")
        # self.assertEqual(effects_sorted[2].prot_pos, None)
        # self.assertEqual(effects_sorted[2].prot_length, None)
        self.assertEqual(effects_sorted[2].aa_change, None)

        self.assertEqual(effects_sorted[3].gene, "HYI")
        self.assertEqual(effects_sorted[3].transcript_id, "NM_031207_1")
        self.assertEqual(effects_sorted[3].strand, "-")
        self.assertEqual(effects_sorted[3].effect, "intron")
        # self.assertEqual(effects_sorted[3].prot_pos, 248)
        # self.assertEqual(effects_sorted[3].prot_length, 248)
        self.assertEqual(effects_sorted[3].aa_change, None)

    def test_chr1_1653031_del_var(self):
        effects = VariantAnnotation.annotate_variant(self.gmDB, self.GA,
                                                     loc="1:1653031",
                                                     var="del(7)")
        self.assertEqual(len(effects), 8)
        effects_sorted = sorted(effects, key=lambda k: k.transcript_id)

        self.assertEqual(effects_sorted[0].gene, "CDK11A")
        self.assertEqual(effects_sorted[0].transcript_id, "NM_024011_1")
        self.assertEqual(effects_sorted[0].strand, "-")
        self.assertEqual(effects_sorted[0].effect, "splice-site")
        # self.assertEqual(effects_sorted[0].prot_pos, 76)
        # self.assertEqual(effects_sorted[0].prot_length, 781)
        self.assertEqual(effects_sorted[0].aa_change, None)

        self.assertEqual(effects_sorted[1].gene, "CDK11B")
        self.assertEqual(effects_sorted[1].transcript_id, "NM_033486_1")
        self.assertEqual(effects_sorted[1].strand, "-")
        self.assertEqual(effects_sorted[1].effect, "splice-site")
        # self.assertEqual(effects_sorted[1].prot_pos, 76)
        # self.assertEqual(effects_sorted[1].prot_length, 781)
        self.assertEqual(effects_sorted[1].aa_change, None)

        self.assertEqual(effects_sorted[2].gene, "CDK11B")
        self.assertEqual(effects_sorted[2].transcript_id, "NM_033487_1")
        self.assertEqual(effects_sorted[2].strand, "-")
        self.assertEqual(effects_sorted[2].effect, "splice-site")
        # self.assertEqual(effects_sorted[2].prot_pos, None)
        # self.assertEqual(effects_sorted[2].prot_length, None)
        self.assertEqual(effects_sorted[2].aa_change, None)

        self.assertEqual(effects_sorted[3].gene, "CDK11B")
        self.assertEqual(effects_sorted[3].transcript_id, "NM_033488_1")
        self.assertEqual(effects_sorted[3].strand, "-")
        self.assertEqual(effects_sorted[3].effect, "splice-site")
        # self.assertEqual(effects_sorted[3].prot_pos, 42)
        # self.assertEqual(effects_sorted[3].prot_length, 736)
        self.assertEqual(effects_sorted[3].aa_change, None)

        self.assertEqual(effects_sorted[4].gene, "CDK11B")
        self.assertEqual(effects_sorted[4].transcript_id, "NM_033489_1")
        self.assertEqual(effects_sorted[4].strand, "-")
        self.assertEqual(effects_sorted[4].effect, "splice-site")
        # self.assertEqual(effects_sorted[4].prot_pos, 42)
        # self.assertEqual(effects_sorted[4].prot_length, 747)
        self.assertEqual(effects_sorted[4].aa_change, None)

        self.assertEqual(effects_sorted[5].gene, "CDK11B")
        self.assertEqual(effects_sorted[5].transcript_id, "NM_033492_1")
        self.assertEqual(effects_sorted[5].strand, "-")
        self.assertEqual(effects_sorted[5].effect, "splice-site")
        # self.assertEqual(effects_sorted[5].prot_pos, 76)
        # self.assertEqual(effects_sorted[5].prot_length, 779)
        self.assertEqual(effects_sorted[5].aa_change, None)

        self.assertEqual(effects_sorted[6].gene, "CDK11B")
        self.assertEqual(effects_sorted[6].transcript_id, "NM_033493_1")
        self.assertEqual(effects_sorted[6].strand, "-")
        self.assertEqual(effects_sorted[6].effect, "splice-site")
        # self.assertEqual(effects_sorted[6].prot_pos, 76)
        # self.assertEqual(effects_sorted[6].prot_length, 770)
        self.assertEqual(effects_sorted[6].aa_change, None)

        self.assertEqual(effects_sorted[7].gene, "CDK11A")
        self.assertEqual(effects_sorted[7].transcript_id, "NM_033529_1")
        self.assertEqual(effects_sorted[7].strand, "-")
        self.assertEqual(effects_sorted[7].effect, "splice-site")
        # self.assertEqual(effects_sorted[7].prot_pos, 76)
        # self.assertEqual(effects_sorted[7].prot_length, 771)
        self.assertEqual(effects_sorted[7].aa_change, None)

    def test_chr3_56627768_del_var(self):
        effects = VariantAnnotation.annotate_variant(self.gmDB, self.GA,
                                                     loc="3:56627768",
                                                     var="del(4)")
        self.assertEqual(len(effects), 3)
        effects_sorted = sorted(effects, key=lambda k: k.transcript_id)

        self.assertEqual(effects_sorted[0].gene, "CCDC66")
        self.assertEqual(effects_sorted[0].transcript_id, "NM_001012506_1")
        self.assertEqual(effects_sorted[0].strand, "+")
        self.assertEqual(effects_sorted[0].effect, "splice-site")
        # self.assertEqual(effects_sorted[0].prot_pos, 406)
        # self.assertEqual(effects_sorted[0].prot_length, 914)
        self.assertEqual(effects_sorted[0].aa_change, None)

        self.assertEqual(effects_sorted[1].gene, "CCDC66")
        self.assertEqual(effects_sorted[1].transcript_id, "NM_001141947_1")
        self.assertEqual(effects_sorted[1].strand, "+")
        self.assertEqual(effects_sorted[1].effect, "splice-site")
        # self.assertEqual(effects_sorted[1].prot_pos, 440)
        # self.assertEqual(effects_sorted[1].prot_length, 948)
        self.assertEqual(effects_sorted[1].aa_change, None)

        self.assertEqual(effects_sorted[2].gene, "CCDC66")
        self.assertEqual(effects_sorted[2].transcript_id, "NR_024460_1")
        self.assertEqual(effects_sorted[2].strand, "+")
        self.assertEqual(effects_sorted[2].effect, "non-coding")
        # self.assertEqual(effects_sorted[2].prot_pos, None)
        # self.assertEqual(effects_sorted[2].prot_length, None)
        self.assertEqual(effects_sorted[2].aa_change, None)

    def test_chr3_172538026_del_var(self):
        effects = VariantAnnotation.annotate_variant(self.gmDB, self.GA,
                                                     loc="3:172538026",
                                                     var="del(6)")
        self.assertEqual(len(effects), 3)
        effects_sorted = sorted(effects, key=lambda k: k.transcript_id)

        self.assertEqual(effects_sorted[0].gene, "ECT2")
        self.assertEqual(effects_sorted[0].transcript_id, "NM_001258315_1")
        self.assertEqual(effects_sorted[0].strand, "+")
        self.assertEqual(effects_sorted[0].effect, "noEnd")
        # self.assertEqual(effects_sorted[0].prot_pos, 915)
        # self.assertEqual(effects_sorted[0].prot_length, 914)
        self.assertEqual(effects_sorted[0].aa_change, None)

        self.assertEqual(effects_sorted[1].gene, "ECT2")
        self.assertEqual(effects_sorted[1].transcript_id, "NM_001258316_1")
        self.assertEqual(effects_sorted[1].strand, "+")
        self.assertEqual(effects_sorted[1].effect, "noEnd")
        # self.assertEqual(effects_sorted[1].prot_pos, 884)
        # self.assertEqual(effects_sorted[1].prot_length, 883)
        self.assertEqual(effects_sorted[1].aa_change, None)

        self.assertEqual(effects_sorted[2].gene, "ECT2")
        self.assertEqual(effects_sorted[2].transcript_id, "NM_018098_1")
        self.assertEqual(effects_sorted[2].strand, "+")
        self.assertEqual(effects_sorted[2].effect, "noEnd")
        # self.assertEqual(effects_sorted[2].prot_pos, 884)
        # self.assertEqual(effects_sorted[2].prot_length, 883)
        self.assertEqual(effects_sorted[2].aa_change, None)

    def test_chr1_29447418_ins_var(self):
        effects = VariantAnnotation.annotate_variant(self.gmDB, self.GA,
                                                     loc="1:29447418",
                                                     var="ins(CAGACCC)")
        self.assertEqual(len(effects), 2)
        effects_sorted = sorted(effects, key=lambda k: k.transcript_id)

        self.assertEqual(effects_sorted[0].gene, "TMEM200B")
        self.assertEqual(effects_sorted[0].transcript_id, "NM_001003682_1")
        self.assertEqual(effects_sorted[0].strand, "-")
        self.assertEqual(effects_sorted[0].effect, "noEnd")
        # self.assertEqual(effects_sorted[0].prot_pos, 308)
        # self.assertEqual(effects_sorted[0].prot_length, 307)
        self.assertEqual(effects_sorted[0].aa_change, None)

        self.assertEqual(effects_sorted[1].gene, "TMEM200B")
        self.assertEqual(effects_sorted[1].transcript_id, "NM_001171868_1")
        self.assertEqual(effects_sorted[1].strand, "-")
        self.assertEqual(effects_sorted[1].effect, "noEnd")
        # self.assertEqual(effects_sorted[1].prot_pos, 308)
        # self.assertEqual(effects_sorted[1].prot_length, 307)
        self.assertEqual(effects_sorted[1].aa_change, None)

    def test_chr6_99817476_del_var(self):
        [effect] = VariantAnnotation.annotate_variant(self.gmDB, self.GA,
                                                      loc="6:99817476",
                                                      var="del(22)")

        self.assertEqual(effect.gene, "COQ3")
        self.assertEqual(effect.transcript_id, "NM_017421_1")
        self.assertEqual(effect.strand, "-")
        self.assertEqual(effect.effect, "noEnd")
        # self.assertEqual(effect.prot_pos, 363)
        # self.assertEqual(effect.prot_length, 369)
        self.assertEqual(effect.aa_change, None)

    def test_last_codon_ins_frameshift_var(self):
        [effect] = VariantAnnotation.annotate_variant(self.gmDB, self.GA,
                                                      loc="7:24727231",
                                                      var="ins(A)")
        self.assertEqual(effect.gene, "MPP6")
        self.assertEqual(effect.transcript_id, "NM_016447_1")
        self.assertEqual(effect.strand, "+")
        self.assertEqual(effect.effect, "noEnd")
        # self.assertEqual(effect.prot_pos, 541)
        # self.assertEqual(effect.prot_length, 540)
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
        self.assertEqual(effects_sorted[0].effect, "splice-site")
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

    def test_chr1_6694147_del_var(self):
        [effect] = VariantAnnotation.annotate_variant(self.gmDB, self.GA,
                                                      loc="1:6694147",
                                                      var="del(3)")

        self.assertEqual(effect.gene, "THAP3")
        self.assertEqual(effect.transcript_id, "NM_138350_1")
        self.assertEqual(effect.strand, "+")
        self.assertEqual(effect.effect, "noEnd")
        # self.assertEqual(effect.prot_pos, 176)
        # self.assertEqual(effect.prot_length, 175)
        self.assertEqual(effect.aa_change, None)

    def test_chr1_23836374_del_var(self):
        [effect] = VariantAnnotation.annotate_variant(self.gmDB, self.GA,
                                                      loc="1:23836374",
                                                      var="del(4)")

        self.assertEqual(effect.gene, "E2F2")
        self.assertEqual(effect.transcript_id, "NM_004091_1")
        self.assertEqual(effect.strand, "-")
        self.assertEqual(effect.effect, "noEnd")
        # self.assertEqual(effect.prot_pos, 437)
        # self.assertEqual(effect.prot_length, 437)
        self.assertEqual(effect.aa_change, None)

    def test_first_codon_ins_var(self):
        [effect] = VariantAnnotation.annotate_variant(self.gmDB, self.GA,
                                                      loc="1:3527831",
                                                      var="ins(A)")
        self.assertEqual(effect.gene, "MEGF6")
        self.assertEqual(effect.transcript_id, "NM_001409_1")
        self.assertEqual(effect.strand, "-")
        self.assertEqual(effect.effect, "noStart")
        # self.assertEqual(effect.prot_pos, 1)
        # self.assertEqual(effect.prot_length, 1541)
        self.assertEqual(effect.aa_change, None)

    def test_chr4_100544005_ins_var(self):
        [effect] = VariantAnnotation.annotate_variant(self.gmDB, self.GA,
                                                      loc="4:100544005",
                                                      var="ins(GAAA)")

        self.assertEqual(effect.gene, "MTTP")
        self.assertEqual(effect.transcript_id, "NM_000253_1")
        self.assertEqual(effect.strand, "+")
        self.assertEqual(effect.effect, "noEnd")
        # self.assertEqual(effect.prot_pos, 895)
        # self.assertEqual(effect.prot_length, 894)
        self.assertEqual(effect.aa_change, None)

    def test_chr6_109954111_del_var(self):
        effects = VariantAnnotation.annotate_variant(self.gmDB, self.GA,
                                                     loc="6:109954111",
                                                     var="del(4)")
        self.assertEqual(len(effects), 2)
        effects_sorted = sorted(effects, key=lambda k: k.transcript_id)

        self.assertEqual(effects_sorted[0].gene, "AK9")
        self.assertEqual(effects_sorted[0].transcript_id, "NM_001145128_1")
        self.assertEqual(effects_sorted[0].strand, "-")
        self.assertEqual(effects_sorted[0].effect, "intron")
        # self.assertEqual(effects_sorted[0].prot_pos, 419)
        # self.assertEqual(effects_sorted[0].prot_length, 1912)
        self.assertEqual(effects_sorted[0].aa_change, None)

        self.assertEqual(effects_sorted[1].gene, "AK9")
        self.assertEqual(effects_sorted[1].transcript_id, "NM_145025_1")
        self.assertEqual(effects_sorted[1].strand, "-")
        self.assertEqual(effects_sorted[1].effect, "noEnd")
        # self.assertEqual(effects_sorted[1].prot_pos, 422)
        # self.assertEqual(effects_sorted[1].prot_length, 422)
        self.assertEqual(effects_sorted[1].aa_change, None)

    def test_chr16_3070391_del_var(self):
        [effect] = VariantAnnotation.annotate_variant(self.gmDB, self.GA,
                                                      loc="16:3070391",
                                                      var="del(13)")

        self.assertEqual(effect.gene, "TNFRSF12A")
        self.assertEqual(effect.transcript_id, "NM_016639_1")
        self.assertEqual(effect.strand, "+")
        self.assertEqual(effect.effect, "noStart")
        # self.assertEqual(effect.prot_pos, 1)
        # self.assertEqual(effect.prot_length, 129)
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

    def test_chr2_47630333_ins_var(self):
        var = "ins(GGCGGTGCAGCCGAAGGA)"
        effects = VariantAnnotation.annotate_variant(self.gmDB, self.GA,
                                                     loc="2:47630333", var=var)
        self.assertEqual(len(effects), 2)
        effects_sorted = sorted(effects, key=lambda k: k.transcript_id)

        self.assertEqual(effects_sorted[0].gene, "MSH2")
        self.assertEqual(effects_sorted[0].transcript_id, "NM_000251_1")
        self.assertEqual(effects_sorted[0].strand, "+")
        # Modified from original, was noStart
        self.assertEqual(effects_sorted[0].effect, "no-frame-shift")
        # self.assertEqual(effects_sorted[0].prot_pos, 1)
        # self.assertEqual(effects_sorted[0].prot_length, 935)
        self.assertEqual(effects_sorted[0].aa_change, None)

        self.assertEqual(effects_sorted[1].gene, "MSH2")
        self.assertEqual(effects_sorted[1].transcript_id, "NM_001258281_1")
        self.assertEqual(effects_sorted[1].strand, "+")
        self.assertEqual(effects_sorted[1].effect, "5'UTR-intron")
        # self.assertEqual(effects_sorted[1].prot_pos, None)
        # self.assertEqual(effects_sorted[1].prot_length, None)
        self.assertEqual(effects_sorted[1].aa_change, None)

    def test_chr2_32853362_ins_var(self):
        effects = VariantAnnotation.annotate_variant(self.gmDB, self.GA,
                                                     loc="2:32853362",
                                                     var="ins(TTTTCTAA)")
        self.assertEqual(len(effects), 2)
        effects_sorted = sorted(effects, key=lambda k: k.transcript_id)

        self.assertEqual(effects_sorted[0].gene, "TTC27")
        self.assertEqual(effects_sorted[0].transcript_id, "NM_001193509_1")
        self.assertEqual(effects_sorted[0].strand, "+")
        self.assertEqual(effects_sorted[0].effect, "5'UTR-intron")
        # self.assertEqual(effects_sorted[0].prot_pos, None)
        # self.assertEqual(effects_sorted[0].prot_length, None)
        self.assertEqual(effects_sorted[0].aa_change, None)

        self.assertEqual(effects_sorted[1].gene, "TTC27")
        self.assertEqual(effects_sorted[1].transcript_id, "NM_017735_1")
        self.assertEqual(effects_sorted[1].strand, "+")
        self.assertEqual(effects_sorted[1].effect, "noStart")
        # self.assertEqual(effects_sorted[1].prot_pos, 1)
        # self.assertEqual(effects_sorted[1].prot_length, 843)
        self.assertEqual(effects_sorted[1].aa_change, None)

    def test_chr20_44518889_ins_var(self):
        effects = VariantAnnotation.annotate_variant(self.gmDB, self.GA,
                                                     loc="20:44518889",
                                                     var="ins(A)")
        self.assertEqual(len(effects), 2)
        effects_sorted = sorted(effects, key=lambda k: k.transcript_id)

        self.assertEqual(effects_sorted[0].gene, "NEURL2")
        self.assertEqual(effects_sorted[0].transcript_id, "NM_001278535_1")
        self.assertEqual(effects_sorted[0].strand, "-")
        self.assertEqual(effects_sorted[0].effect, "frame-shift")
        # self.assertEqual(effects_sorted[0].prot_pos, 248)
        # self.assertEqual(effects_sorted[0].prot_length, 262)
        self.assertEqual(effects_sorted[0].aa_change, None)

        self.assertEqual(effects_sorted[1].gene, "NEURL2")
        self.assertEqual(effects_sorted[1].transcript_id, "NM_080749_1")
        self.assertEqual(effects_sorted[1].strand, "-")
        self.assertEqual(effects_sorted[1].effect, "frame-shift")
        # self.assertEqual(effects_sorted[1].prot_pos, 248)
        # self.assertEqual(effects_sorted[1].prot_length, 286)
        self.assertEqual(effects_sorted[1].aa_change, None)

    def test_chr9_139839774_ins_var(self):
        var = "ins(TGCTGCCGCCACCA)"
        [effect] = VariantAnnotation.annotate_variant(self.gmDB, self.GA,
                                                      loc="9:139839774",
                                                      var=var)

        self.assertEqual(effect.gene, "C8G")
        self.assertEqual(effect.transcript_id, "NM_000606_1")
        self.assertEqual(effect.strand, "+")
        self.assertEqual(effect.effect, "frame-shift")
        # self.assertEqual(effect.prot_pos, None)
        # self.assertEqual(effect.prot_length, None)
        self.assertEqual(effect.aa_change, None)

    def test_chr1_17313765_ins_var(self):
        effects = VariantAnnotation.annotate_variant(self.gmDB, self.GA,
                                                     loc="1:17313765",
                                                     var="ins(C)")
        self.assertEqual(len(effects), 3)
        effects_sorted = sorted(effects, key=lambda k: k.transcript_id)

        self.assertEqual(effects_sorted[0].gene, "ATP13A2")
        self.assertEqual(effects_sorted[0].transcript_id, "NM_001141973_1")
        self.assertEqual(effects_sorted[0].strand, "-")
        self.assertEqual(effects_sorted[0].effect, "frame-shift")
        # self.assertEqual(effects_sorted[0].prot_pos, 949)
        # self.assertEqual(effects_sorted[0].prot_length, 1176)
        self.assertEqual(effects_sorted[0].aa_change, None)

        self.assertEqual(effects_sorted[1].gene, "ATP13A2")
        self.assertEqual(effects_sorted[1].transcript_id, "NM_001141974_1")
        self.assertEqual(effects_sorted[1].strand, "-")
        self.assertEqual(effects_sorted[1].effect, "frame-shift")
        # self.assertEqual(effects_sorted[1].prot_pos, 910)
        # self.assertEqual(effects_sorted[1].prot_length, 1159)
        self.assertEqual(effects_sorted[1].aa_change, None)

        self.assertEqual(effects_sorted[2].gene, "ATP13A2")
        self.assertEqual(effects_sorted[2].transcript_id, "NM_022089_1")
        self.assertEqual(effects_sorted[2].strand, "-")
        self.assertEqual(effects_sorted[2].effect, "frame-shift")
        # self.assertEqual(effects_sorted[2].prot_pos, 954)
        # self.assertEqual(effects_sorted[2].prot_length, 1181)
        self.assertEqual(effects_sorted[2].aa_change, None)

    def test_chr13_45911524_ins_var(self):
        var = "ins(ACATTTTTCCATTTCTAAACCAT)"
        [effect] = VariantAnnotation.annotate_variant(self.gmDB, self.GA,
                                                      loc="13:45911524",
                                                      var=var)

        self.assertEqual(effect.gene, "TPT1")
        self.assertEqual(effect.transcript_id, "NM_003295_1")
        self.assertEqual(effect.strand, "-")
        self.assertEqual(effect.effect, "frame-shift")
        # self.assertEqual(effect.prot_pos, 173)
        # self.assertEqual(effect.prot_length, 173)
        self.assertEqual(effect.aa_change, None)

    def test_chr1_906785_ins_var(self):
        var = "ins(GTGGGCCCCTCCCCACT)"
        effects = VariantAnnotation.annotate_variant(self.gmDB, self.GA,
                                                     loc="1:906785", var=var)
        self.assertEqual(len(effects), 2)
        effects_sorted = sorted(effects, key=lambda k: k.transcript_id)

        self.assertEqual(effects_sorted[0].gene, "PLEKHN1")
        self.assertEqual(effects_sorted[0].transcript_id, "NM_001160184_1")
        self.assertEqual(effects_sorted[0].strand, "+")
        self.assertEqual(effects_sorted[0].effect, "frame-shift")
        # self.assertEqual(effects_sorted[0].prot_pos, 275)
        # self.assertEqual(effects_sorted[0].prot_length, 577)
        self.assertEqual(effects_sorted[0].aa_change, None)

        self.assertEqual(effects_sorted[1].gene, "PLEKHN1")
        self.assertEqual(effects_sorted[1].transcript_id, "NM_032129_1")
        self.assertEqual(effects_sorted[1].strand, "+")
        self.assertEqual(effects_sorted[1].effect, "frame-shift")
        # self.assertEqual(effects_sorted[1].prot_pos, 263)
        # self.assertEqual(effects_sorted[1].prot_length, 612)
        self.assertEqual(effects_sorted[1].aa_change, None)

    def test_chr1_45446840_ins_var(self):
        effects = VariantAnnotation.annotate_variant(self.gmDB, self.GA,
                                                     loc="1:45446840",
                                                     var="ins(T)")

        self.assertEqual(len(effects), 3)
        effects_sorted = sorted(effects, key=lambda k: k.transcript_id)

        self.assertEqual(effects_sorted[0].gene, "EIF2B3")
        self.assertEqual(effects_sorted[0].transcript_id, "NM_001166588_1")
        self.assertEqual(effects_sorted[0].strand, "-")
        self.assertEqual(effects_sorted[0].effect, "5'UTR")
        # self.assertEqual(effect.prot_pos, None)
        # self.assertEqual(effect.prot_length, None)
        self.assertEqual(effects_sorted[0].aa_change, None)

        self.assertEqual(effects_sorted[1].gene, "EIF2B3")
        self.assertEqual(effects_sorted[1].transcript_id, "NM_001261418_1")
        self.assertEqual(effects_sorted[1].strand, "-")
        self.assertEqual(effects_sorted[1].effect, "5'UTR")
        # self.assertEqual(effect.prot_pos, None)
        # self.assertEqual(effect.prot_length, None)
        self.assertEqual(effects_sorted[1].aa_change, None)

        self.assertEqual(effects_sorted[2].gene, "EIF2B3")
        self.assertEqual(effects_sorted[2].transcript_id, "NM_020365_1")
        self.assertEqual(effects_sorted[2].strand, "-")
        self.assertEqual(effects_sorted[2].effect, "5'UTR")
        # self.assertEqual(effect.prot_pos, None)
        # self.assertEqual(effect.prot_length, None)
        self.assertEqual(effects_sorted[2].aa_change, None)

    def test_chr1_31845860_ins_var(self):
        [effect] = VariantAnnotation.annotate_variant(self.gmDB, self.GA,
                                                      loc="1:31845860",
                                                      var="ins(ATAG)")

        self.assertEqual(effect.gene, "FABP3")
        self.assertEqual(effect.transcript_id, "NM_004102_1")
        self.assertEqual(effect.strand, "-")
        self.assertEqual(effect.effect, "5'UTR")
        # self.assertEqual(effect.prot_pos, None)
        # self.assertEqual(effect.prot_length, None)
        self.assertEqual(effect.aa_change, None)

    def test_chr1_47775990_del_var(self):
        effects = VariantAnnotation.annotate_variant(self.gmDB, self.GA,
                                                     loc="1:47775990",
                                                     var="del(3)")
        self.assertEqual(len(effects), 2)
        effects_sorted = sorted(effects, key=lambda k: k.transcript_id)

        self.assertEqual(effects_sorted[0].gene, "STIL")
        self.assertEqual(effects_sorted[0].transcript_id, "NM_001048166_1")
        self.assertEqual(effects_sorted[0].strand, "-")
        self.assertEqual(effects_sorted[0].effect, "5'UTR")
        # self.assertEqual(effects_sorted[0].prot_pos, 1)
        # self.assertEqual(effects_sorted[0].prot_length, 1288)
        self.assertEqual(effects_sorted[0].aa_change, None)

        self.assertEqual(effects_sorted[1].gene, "STIL")
        self.assertEqual(effects_sorted[1].transcript_id, "NM_003035_1")
        self.assertEqual(effects_sorted[1].strand, "-")
        self.assertEqual(effects_sorted[1].effect, "5'UTR")
        # self.assertEqual(effects_sorted[1].prot_pos, 1)
        # self.assertEqual(effects_sorted[1].prot_length, 1287)
        self.assertEqual(effects_sorted[1].aa_change, None)

    def test_chr1_120387156_sub_var(self):
        [effect] = VariantAnnotation.annotate_variant(self.gmDB, self.GA,
                                                      loc="1:120387156",
                                                      var="sub(C->T)")

        self.assertEqual(effect.gene, "NBPF7")
        self.assertEqual(effect.transcript_id, "NM_001047980_1")
        self.assertEqual(effect.strand, "-")
        self.assertEqual(effect.effect, "frame-shift")
        # self.assertEqual(effect.prot_pos, 1)
        # self.assertEqual(effect.prot_length, 422)
        self.assertEqual(effect.aa_change, None)

    def test_chr11_128868319_ins_var(self):
        var = "ins(AATTTCACAATCACCTATTTCTGGTACTTAGCAACATCACAGGTAGATCCTGCCTTC"\
            "ATCTTCTGGCATTTC)"
        effects = VariantAnnotation.annotate_variant(self.gmDB, self.GA,
                                                     loc="11:128868319",
                                                     var=var)
        self.assertEqual(len(effects), 2)
        effects_sorted = sorted(effects, key=lambda k: k.transcript_id)

        self.assertEqual(effects_sorted[0].gene, "ARHGAP32")
        self.assertEqual(effects_sorted[0].transcript_id, "NM_001142685_1")
        self.assertEqual(effects_sorted[0].strand, "-")
        self.assertEqual(effects_sorted[0].effect, "no-frame-shift-newStop")
        # self.assertEqual(effects_sorted[0].prot_pos, 350)
        # self.assertEqual(effects_sorted[0].prot_length, 2087)
        self.assertEqual(effects_sorted[0].aa_change, None)

        self.assertEqual(effects_sorted[1].gene, "ARHGAP32")
        self.assertEqual(effects_sorted[1].transcript_id, "NM_014715_1")
        self.assertEqual(effects_sorted[1].strand, "-")
        self.assertEqual(effects_sorted[1].effect, "no-frame-shift")
        # self.assertEqual(effects_sorted[1].prot_pos, 1)
        # self.assertEqual(effects_sorted[1].prot_length, 1739)
        self.assertEqual(effects_sorted[1].aa_change, None)

    def test_chr1_38061419_del_var(self):
        [effect] = VariantAnnotation.annotate_variant(self.gmDB, self.GA,
                                                      loc="1:38061419",
                                                      var="del(17)")

        self.assertEqual(effect.gene, "GNL2")
        self.assertEqual(effect.transcript_id, "NM_013285_1")
        self.assertEqual(effect.strand, "-")
        self.assertEqual(effect.effect, "noStart")
        # self.assertEqual(effect.prot_pos, 1)
        # self.assertEqual(effect.prot_length, 731)
        self.assertEqual(effect.aa_change, None)

    def test_first_codon_ins_integenic_var(self):
        [effect] = VariantAnnotation.annotate_variant(self.gmDB, self.GA,
                                                      loc="1:3407092",
                                                      var="ins(A)")
        self.assertEqual(effect.gene, "MEGF6")
        self.assertEqual(effect.transcript_id, "NM_001409_1")
        self.assertEqual(effect.strand, "-")
        self.assertEqual(effect.effect, "noEnd")
        # self.assertEqual(effect.prot_pos, None)
        # self.assertEqual(effect.prot_length, None)
        self.assertEqual(effect.aa_change, None)

    def test_chr1_92546129_ins_var(self):
        [effect] = VariantAnnotation.annotate_variant(self.gmDB, self.GA,
                                                      loc="1:92546129",
                                                      var="ins(A)")

        self.assertEqual(effect.gene, "BTBD8")
        self.assertEqual(effect.transcript_id, "NM_183242_1")
        self.assertEqual(effect.strand, "+")
        self.assertEqual(effect.effect, "5'UTR")
        # self.assertEqual(effect.prot_pos, None)
        # self.assertEqual(effect.prot_length, None)
        self.assertEqual(effect.aa_change, None)

    def test_chr1_11740658_ins_var(self):
        effects = VariantAnnotation.annotate_variant(self.gmDB, self.GA,
                                                     loc="1:11740658",
                                                     var="ins(TCCT)")

        self.assertEqual(len(effects), 2)
        effects_sorted = sorted(effects, key=lambda k: k.transcript_id)

        self.assertEqual(effects_sorted[0].gene, "MAD2L2")
        self.assertEqual(effects_sorted[0].transcript_id, "NM_001127325_1")
        self.assertEqual(effects_sorted[0].strand, "-")
        self.assertEqual(effects_sorted[0].effect, "5'UTR")
        # self.assertEqual(effect.prot_pos, None)
        # self.assertEqual(effect.prot_length, None)
        self.assertEqual(effects_sorted[0].aa_change, None)

        self.assertEqual(effects_sorted[1].gene, "MAD2L2")
        self.assertEqual(effects_sorted[1].transcript_id, "NM_006341_1")
        self.assertEqual(effects_sorted[1].strand, "-")
        self.assertEqual(effects_sorted[1].effect, "5'UTR")
        # self.assertEqual(effect.prot_pos, None)
        # self.assertEqual(effect.prot_length, None)
        self.assertEqual(effects_sorted[1].aa_change, None)

    def test_chr6_161557574_ins_var(self):
        [effect] = VariantAnnotation.annotate_variant(self.gmDB, self.GA,
                                                      loc="6:161557574",
                                                      var="ins(AGTC)")

        self.assertEqual(effect.gene, "AGPAT4")
        self.assertEqual(effect.transcript_id, "NM_020133_1")
        self.assertEqual(effect.strand, "-")
        self.assertEqual(effect.effect, "no-frame-shift")
        # self.assertEqual(effect.prot_pos, None)
        # self.assertEqual(effect.prot_length, None)
        self.assertEqual(effect.aa_change, None)

    def test_chr11_123847404_ins_var(self):
        [effect] = VariantAnnotation.annotate_variant(self.gmDB, self.GA,
                                                      loc="11:123847404",
                                                      var="ins(T)")

        self.assertEqual(effect.gene, None)
        self.assertEqual(effect.transcript_id, None)
        self.assertEqual(effect.strand, None)
        self.assertEqual(effect.effect, "intergenic")
        # self.assertEqual(effect.prot_pos, None)
        # self.assertEqual(effect.prot_length, None)
        self.assertEqual(effect.aa_change, None)

    def test_chr1_26158517_ins_var(self):
        effects = VariantAnnotation.annotate_variant(self.gmDB, self.GA,
                                                     loc="1:26158517",
                                                     var="ins(ACA)")
        self.assertEqual(len(effects), 4)
        effects_sorted = sorted(effects, key=lambda k: k.transcript_id)

        self.assertEqual(effects_sorted[0].gene, "MTFR1L")
        self.assertEqual(effects_sorted[0].transcript_id, "NM_001099625_1")
        self.assertEqual(effects_sorted[0].strand, "+")
        self.assertEqual(effects_sorted[0].effect, "3'UTR")
        # self.assertEqual(effect.prot_pos, None)
        # self.assertEqual(effect.prot_length, None)
        self.assertEqual(effects_sorted[0].aa_change, None)

        self.assertEqual(effects_sorted[1].gene, "MTFR1L")
        self.assertEqual(effects_sorted[1].transcript_id, "NM_001099626_1")
        self.assertEqual(effects_sorted[1].strand, "+")
        self.assertEqual(effects_sorted[1].effect, "3'UTR")
        # self.assertEqual(effect.prot_pos, None)
        # self.assertEqual(effect.prot_length, None)
        self.assertEqual(effects_sorted[1].aa_change, None)

        self.assertEqual(effects_sorted[2].gene, "MTFR1L")
        self.assertEqual(effects_sorted[2].transcript_id, "NM_001099627_1")
        self.assertEqual(effects_sorted[2].strand, "+")
        self.assertEqual(effects_sorted[2].effect, "3'UTR")
        # self.assertEqual(effect.prot_pos, None)
        # self.assertEqual(effect.prot_length, None)
        self.assertEqual(effects_sorted[2].aa_change, None)

        self.assertEqual(effects_sorted[3].gene, "MTFR1L")
        self.assertEqual(effects_sorted[3].transcript_id, "NM_019557_1")
        self.assertEqual(effects_sorted[3].strand, "+")
        self.assertEqual(effects_sorted[3].effect, "3'UTR")
        # self.assertEqual(effect.prot_pos, None)
        # self.assertEqual(effect.prot_length, None)
        self.assertEqual(effects_sorted[3].aa_change, None)

    def test_last_codon_ins_intergenic_var(self):
        [effect] = VariantAnnotation.annotate_variant(self.gmDB, self.GA,
                                                      loc="7:24727232",
                                                      var="ins(A)")
        self.assertEqual(effect.gene, "MPP6")
        self.assertEqual(effect.transcript_id, "NM_016447_1")
        self.assertEqual(effect.strand, "+")
        self.assertEqual(effect.effect, "3'UTR")
        # self.assertEqual(effect.prot_pos, None)
        # self.assertEqual(effect.prot_length, None)
        self.assertEqual(effect.aa_change, None)

    def test_chr7_149461804_del_var(self):
        [effect] = VariantAnnotation.annotate_variant(self.gmDB, self.GA,
                                                      loc="7:149461804",
                                                      var="del(1)")

        self.assertEqual(effect.gene, "ZNF467")
        self.assertEqual(effect.transcript_id, "NM_207336_1")
        self.assertEqual(effect.strand, "-")
        self.assertEqual(effect.effect, "3'UTR")
        # self.assertEqual(effect.prot_pos, 596)
        # self.assertEqual(effect.prot_length, 595)
        self.assertEqual(effect.aa_change, None)

    def test_chr1_44686290_ins_var(self):
        effects = VariantAnnotation.annotate_variant(self.gmDB, self.GA,
                                                     loc="1:44686290",
                                                     var="ins(A)")

        self.assertEqual(len(effects), 3)
        effects_sorted = sorted(effects, key=lambda k: k.transcript_id)

        self.assertEqual(effects_sorted[0].gene, "DMAP1")
        self.assertEqual(effects_sorted[0].transcript_id, "NM_001034023_1")
        self.assertEqual(effects_sorted[0].strand, "+")
        self.assertEqual(effects_sorted[0].effect, "3'UTR")
        # self.assertEqual(effect.prot_pos, None)
        # self.assertEqual(effect.prot_length, None)
        self.assertEqual(effects_sorted[0].aa_change, None)

        self.assertEqual(effects_sorted[1].gene, "DMAP1")
        self.assertEqual(effects_sorted[1].transcript_id, "NM_001034024_1")
        self.assertEqual(effects_sorted[1].strand, "+")
        self.assertEqual(effects_sorted[1].effect, "3'UTR")
        # self.assertEqual(effect.prot_pos, None)
        # self.assertEqual(effect.prot_length, None)
        self.assertEqual(effects_sorted[1].aa_change, None)

        self.assertEqual(effects_sorted[2].gene, "DMAP1")
        self.assertEqual(effects_sorted[2].transcript_id, "NM_019100_1")
        self.assertEqual(effects_sorted[2].strand, "+")
        self.assertEqual(effects_sorted[2].effect, "3'UTR")
        # self.assertEqual(effect.prot_pos, None)
        # self.assertEqual(effect.prot_length, None)
        self.assertEqual(effects_sorted[2].aa_change, None)

    def test_chr1_26142208_ins_var(self):
        effects = VariantAnnotation.annotate_variant(self.gmDB, self.GA,
                                                     loc="1:26142208",
                                                     var="ins(AG)")

        self.assertEqual(len(effects), 2)
        effects_sorted = sorted(effects, key=lambda k: k.transcript_id)

        self.assertEqual(effects_sorted[0].gene, "SEPN1")
        self.assertEqual(effects_sorted[0].transcript_id, "NM_020451_1")
        self.assertEqual(effects_sorted[0].strand, "+")
        self.assertEqual(effects_sorted[0].effect, "3'UTR")
        # self.assertEqual(effect.prot_pos, None)
        # self.assertEqual(effect.prot_length, None)
        self.assertEqual(effects_sorted[0].aa_change, None)

        self.assertEqual(effects_sorted[1].gene, "SEPN1")
        self.assertEqual(effects_sorted[1].transcript_id, "NM_206926_1")
        self.assertEqual(effects_sorted[1].strand, "+")
        self.assertEqual(effects_sorted[1].effect, "3'UTR")
        # self.assertEqual(effect.prot_pos, None)
        # self.assertEqual(effect.prot_length, None)
        self.assertEqual(effects_sorted[1].aa_change, None)

    def test_chr12_125396262_ins_var(self):
        [effect] = VariantAnnotation.annotate_variant(self.gmDB, self.GA,
                                                      loc="12:125396262",
                                                      var="ins(T)")

        self.assertEqual(effect.gene, "UBC")
        self.assertEqual(effect.transcript_id, "NM_021009_1")
        self.assertEqual(effect.strand, "-")
        self.assertEqual(effect.effect, "3'UTR")
        # self.assertEqual(effect.prot_pos, None)
        # self.assertEqual(effect.prot_length, None)
        self.assertEqual(effect.aa_change, None)

    def test_chr1_16890438_del_var(self):
        [effect] = VariantAnnotation.annotate_variant(self.gmDB, self.GA,
                                                      loc="1:16890438",
                                                      var="del(1)")

        self.assertEqual(effect.gene, "NBPF1")
        self.assertEqual(effect.transcript_id, "NM_017940_1")
        self.assertEqual(effect.strand, "-")
        self.assertEqual(effect.effect, "3'UTR")
        # self.assertEqual(effect.prot_pos, 1142)
        # self.assertEqual(effect.prot_length, 1141)
        self.assertEqual(effect.aa_change, None)


if __name__ == "__main__":
    unittest.main()
