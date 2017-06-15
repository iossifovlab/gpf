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

    def test_synonymous_sub_var(self):
        [effect] = VariantAnnotation.annotate_variant(self.gmDB, self.GA,
                                                      loc="1:897349",
                                                      var="sub(G->A)")
        self.assert_chr1_897349_sub(effect)

    def test_synonymous_sub_ref_alt(self):
        [effect] = VariantAnnotation.annotate_variant(self.gmDB, self.GA,
                                                      loc="1:897349",
                                                      ref="G",
                                                      alt="A")
        self.assert_chr1_897349_sub(effect)

    def test_synonymous_sub_ref_alt_pos(self):
        [effect] = VariantAnnotation.annotate_variant(self.gmDB, self.GA,
                                                      chr="1",
                                                      position="897349",
                                                      ref="G",
                                                      alt="A")
        self.assert_chr1_897349_sub(effect)

    def test_reverse_strand_frame_shift_var(self):
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

    def test_intron_var(self):
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

    def test_frame_shift_var(self):
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

    def test_no_frame_shift_var(self):
        effects = VariantAnnotation.annotate_variant(self.gmDB, self.GA,
                                                     loc="1:24507340",
                                                     var="del(3)")
        self.assertEqual(len(effects), 3)

        self.assertEqual(effects[0].gene, "IFNLR1")
        self.assertEqual(effects[0].transcript_id, "NM_173065_1")
        self.assertEqual(effects[0].strand, "-")
        self.assertEqual(effects[0].effect, "no-frame-shift")
        self.assertEqual(effects[0].prot_pos, 21)
        self.assertEqual(effects[0].prot_length, 244)
        self.assertEqual(effects[0].aa_change, None)

        self.assertEqual(effects[1].gene, "IFNLR1")
        self.assertEqual(effects[1].transcript_id, "NM_173064_1")
        self.assertEqual(effects[1].strand, "-")
        self.assertEqual(effects[1].effect, "no-frame-shift")
        self.assertEqual(effects[1].prot_pos, 21)
        self.assertEqual(effects[1].prot_length, 491)
        self.assertEqual(effects[1].aa_change, None)

        self.assertEqual(effects[2].gene, "IFNLR1")
        self.assertEqual(effects[2].transcript_id, "NM_170743_1")
        self.assertEqual(effects[2].strand, "-")
        self.assertEqual(effects[2].effect, "no-frame-shift")
        self.assertEqual(effects[2].prot_pos, 21)
        self.assertEqual(effects[2].prot_length, 520)
        self.assertEqual(effects[2].aa_change, None)

    def test_nonsense_var(self):
        effects = VariantAnnotation.annotate_variant(self.gmDB, self.GA,
                                                     loc="1:61553905",
                                                     var="sub(C->T)")
        self.assertEqual(len(effects), 4)

        self.assertEqual(effects[0].gene, "NFIA")
        self.assertEqual(effects[0].transcript_id, "NM_001145512_1")
        self.assertEqual(effects[0].strand, "+")
        self.assertEqual(effects[0].effect, "nonsense")
        self.assertEqual(effects[0].prot_pos, 83)
        self.assertEqual(effects[0].prot_length, 554)
        self.assertEqual(effects[0].aa_change, "Arg->End")

        self.assertEqual(effects[1].gene, "NFIA")
        self.assertEqual(effects[1].transcript_id, "NM_001145511_1")
        self.assertEqual(effects[1].strand, "+")
        self.assertEqual(effects[1].effect, "nonsense")
        self.assertEqual(effects[1].prot_pos, 30)
        self.assertEqual(effects[1].prot_length, 501)
        self.assertEqual(effects[1].aa_change, "Arg->End")

        self.assertEqual(effects[2].gene, "NFIA")
        self.assertEqual(effects[2].transcript_id, "NM_001134673_1")
        self.assertEqual(effects[2].strand, "+")
        self.assertEqual(effects[2].effect, "nonsense")
        self.assertEqual(effects[2].prot_pos, 38)
        self.assertEqual(effects[2].prot_length, 509)
        self.assertEqual(effects[2].aa_change, "Arg->End")

        self.assertEqual(effects[3].gene, "NFIA")
        self.assertEqual(effects[3].transcript_id, "NM_005595_1")
        self.assertEqual(effects[3].strand, "+")
        self.assertEqual(effects[3].effect, "nonsense")
        self.assertEqual(effects[3].prot_pos, 38)
        self.assertEqual(effects[3].prot_length, 498)
        self.assertEqual(effects[3].aa_change, "Arg->End")

    def test_splice_site_var(self):
        effects = VariantAnnotation.annotate_variant(self.gmDB, self.GA,
                                                     loc="1:67878948",
                                                     var="sub(T->G)")
        self.assertEqual(len(effects), 4)

        self.assertEqual(effects[0].gene, "SERBP1")
        self.assertEqual(effects[0].transcript_id, "NM_015640_1")
        self.assertEqual(effects[0].strand, "-")
        self.assertEqual(effects[0].effect, "splice-site")
        self.assertEqual(effects[0].prot_pos, 370)
        self.assertEqual(effects[0].prot_length, 388)
        self.assertEqual(effects[0].aa_change, None)

        self.assertEqual(effects[1].gene, "SERBP1")
        self.assertEqual(effects[1].transcript_id, "NM_001018067_1")
        self.assertEqual(effects[1].strand, "-")
        self.assertEqual(effects[1].effect, "splice-site")
        self.assertEqual(effects[1].prot_pos, 391)
        self.assertEqual(effects[1].prot_length, 409)
        self.assertEqual(effects[1].aa_change, None)

        self.assertEqual(effects[2].gene, "SERBP1")
        self.assertEqual(effects[2].transcript_id, "NM_001018068_1")
        self.assertEqual(effects[2].strand, "-")
        self.assertEqual(effects[2].effect, "splice-site")
        self.assertEqual(effects[2].prot_pos, 385)
        self.assertEqual(effects[2].prot_length, 403)
        self.assertEqual(effects[2].aa_change, None)

        self.assertEqual(effects[3].gene, "SERBP1")
        self.assertEqual(effects[3].transcript_id, "NM_001018069_1")
        self.assertEqual(effects[3].strand, "-")
        self.assertEqual(effects[3].effect, "splice-site")
        self.assertEqual(effects[3].prot_pos, 376)
        self.assertEqual(effects[3].prot_length, 394)
        self.assertEqual(effects[3].aa_change, None)

    def test_no_frame_shift_newStop_var(self):
        [effect] = VariantAnnotation.annotate_variant(self.gmDB, self.GA,
                                                      loc="17:17697260",
                                                      var="ins(AGT)")
        self.assertEqual(effect.gene, "RAI1")
        self.assertEqual(effect.transcript_id, "NM_030665_1")
        self.assertEqual(effect.strand, "+")
        self.assertEqual(effect.effect, "no-frame-shift-newStop")
        self.assertEqual(effect.prot_pos, 333)
        self.assertEqual(effect.prot_length, 1906)
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
        self.assertEqual(effects[0].prot_pos, 68)
        self.assertEqual(effects[0].prot_length, 190)

        self.assertEqual(effects[1].transcript_id, "NM_001206983_1")
        self.assertEqual(effects[1].effect, "no-frame-shift")
        self.assertEqual(effects[1].prot_pos, 68)
        self.assertEqual(effects[1].prot_length, 190)

        self.assertEqual(effects[2].transcript_id, "NM_001206985_1")
        self.assertEqual(effects[2].effect, "noStart")
        self.assertEqual(effects[2].prot_pos, 1)
        self.assertEqual(effects[2].prot_length, 124)

        self.assertEqual(effects[3].transcript_id, "NM_001206987_1")
        self.assertEqual(effects[3].effect, "noStart")
        self.assertEqual(effects[3].prot_pos, 1)
        self.assertEqual(effects[3].prot_length, 124)

        self.assertEqual(effects[4].transcript_id, "NM_001206986_1")
        self.assertEqual(effects[4].effect, "noStart")
        self.assertEqual(effects[4].prot_pos, 1)
        self.assertEqual(effects[4].prot_length, 124)

        self.assertEqual(effects[5].transcript_id, "NR_038193_1")
        self.assertEqual(effects[5].effect, "non-coding-intron")
        self.assertEqual(effects[5].prot_pos, None)
        self.assertEqual(effects[5].prot_length, None)

        self.assertEqual(effects[6].transcript_id, "NM_001080510_1")
        self.assertEqual(effects[6].effect, "no-frame-shift")
        self.assertEqual(effects[6].prot_pos, 68)
        self.assertEqual(effects[6].prot_length, 190)

    def test_no_end_var(self):
        [effect] = VariantAnnotation.annotate_variant(self.gmDB, self.GA,
                                                      loc="19:8645778",
                                                      var="del(9)")
        self.assertEqual(effect.gene, "ADAMTS10")
        self.assertEqual(effect.transcript_id, "NM_030957_1")
        self.assertEqual(effect.strand, "-")
        self.assertEqual(effect.effect, "noEnd")
        self.assertEqual(effect.prot_pos, 1104)
        self.assertEqual(effect.prot_length, 1104)
        self.assertEqual(effect.aa_change, None)

    def test_intergenic_var(self):
        [effect] = VariantAnnotation.annotate_variant(self.gmDB, self.GA,
                                                      loc="1:20421037",
                                                      var="sub(G->A)")
        self.assertEqual(effect.gene, None)
        self.assertEqual(effect.transcript_id, None)
        self.assertEqual(effect.strand, None)
        self.assertEqual(effect.effect, "intergenic")
        self.assertEqual(effect.prot_pos, None)
        self.assertEqual(effect.prot_length, None)
        self.assertEqual(effect.aa_change, None)

    def test_3_UTR_var(self):
        effects = VariantAnnotation.annotate_variant(self.gmDB, self.GA,
                                                     loc="1:47013144",
                                                     var="sub(G->A)")

        self.assertEqual(len(effects), 2)

        self.assertEqual(effects[0].gene, "KNCN")
        self.assertEqual(effects[0].transcript_id, "NM_001097611_1")
        self.assertEqual(effects[0].strand, "-")
        self.assertEqual(effects[0].effect, "3'UTR")
        self.assertEqual(effects[0].prot_pos, None)
        self.assertEqual(effects[0].prot_length, None)
        self.assertEqual(effects[0].aa_change, None)

        self.assertEqual(effects[1].gene, "MKNK1-AS1")
        self.assertEqual(effects[1].transcript_id, "NR_038403_1")
        self.assertEqual(effects[1].strand, "+")
        self.assertEqual(effects[1].effect, "non-coding-intron")
        self.assertEqual(effects[1].prot_pos, None)
        self.assertEqual(effects[1].prot_length, None)
        self.assertEqual(effects[1].aa_change, None)

    def test_5_UTR_var(self):
        [effect] = VariantAnnotation.annotate_variant(self.gmDB, self.GA,
                                                      loc="1:57284965",
                                                      var="sub(G->A)")
        self.assertEqual(effect.gene, "C1orf168")
        self.assertEqual(effect.transcript_id, "NM_001004303_1")
        self.assertEqual(effect.strand, "-")
        self.assertEqual(effect.effect, "5'UTR")
        self.assertEqual(effect.prot_pos, None)
        self.assertEqual(effect.prot_length, None)
        self.assertEqual(effect.aa_change, None)

    def test_first_codon_ins_var(self):
        [effect] = VariantAnnotation.annotate_variant(self.gmDB, self.GA,
                                                      loc="1:3527831",
                                                      var="ins(A)")
        self.assertEqual(effect.gene, "MEGF6")
        self.assertEqual(effect.transcript_id, "NM_001409_1")
        self.assertEqual(effect.strand, "-")
        self.assertEqual(effect.effect, "frame-shift")
        self.assertEqual(effect.prot_pos, 1)
        self.assertEqual(effect.prot_length, 1541)
        self.assertEqual(effect.aa_change, None)

    def test_middle_codon_sub_var(self):
        [effect] = VariantAnnotation.annotate_variant(self.gmDB, self.GA,
                                                      loc="1:897348",
                                                      var="sub(A->G)")
        self.assertEqual(effect.gene, "KLHL17")
        self.assertEqual(effect.transcript_id, "NM_198317_1")
        self.assertEqual(effect.strand, "+")
        self.assertEqual(effect.effect, "missense")
        self.assertEqual(effect.prot_pos, 211)
        self.assertEqual(effect.prot_length, 642)
        self.assertEqual(effect.aa_change, "Lys->Arg")

    def test_splice_site_del_pos_strand_var(self):
        [effect] = VariantAnnotation.annotate_variant(self.gmDB, self.GA,
                                                      loc="7:24720141",
                                                      var="del(1)")
        self.assertEqual(effect.gene, "MPP6")
        self.assertEqual(effect.transcript_id, "NM_016447_1")
        self.assertEqual(effect.strand, "+")
        self.assertEqual(effect.effect, "splice-site")
        self.assertEqual(effect.prot_pos, 482)
        self.assertEqual(effect.prot_length, 541)
        self.assertEqual(effect.aa_change, None)

    def test_splice_site_del_neg_strand_var(self):
        [effect] = VariantAnnotation.annotate_variant(self.gmDB, self.GA,
                                                      loc="4:48523230",
                                                      var="del(4)")
        self.assertEqual(effect.gene, "FRYL")
        self.assertEqual(effect.transcript_id, "NM_015030_1")
        self.assertEqual(effect.strand, "-")
        self.assertEqual(effect.effect, "splice-site")
        self.assertEqual(effect.prot_pos, 2508)
        self.assertEqual(effect.prot_length, 3014)
        self.assertEqual(effect.aa_change, None)

    def test_splice_site_ins_pos_strand_var(self):
        [effect] = VariantAnnotation.annotate_variant(self.gmDB, self.GA,
                                                      loc="7:24720141",
                                                      var="ins(C)")
        self.assertEqual(effect.gene, "MPP6")
        self.assertEqual(effect.transcript_id, "NM_016447_1")
        self.assertEqual(effect.strand, "+")
        self.assertEqual(effect.effect, "splice-site")
        self.assertEqual(effect.prot_pos, 482)
        self.assertEqual(effect.prot_length, 541)
        self.assertEqual(effect.aa_change, None)

    def test_splice_site_ins_neg_strand_var(self):
        [effect] = VariantAnnotation.annotate_variant(self.gmDB, self.GA,
                                                      loc="12:116418554",
                                                      var="ins(C)")
        self.assertEqual(effect.gene, "MED13L")
        self.assertEqual(effect.transcript_id, "NM_015335_1")
        self.assertEqual(effect.strand, "-")
        self.assertEqual(effect.effect, "splice-site")
        self.assertEqual(effect.prot_pos, 1789)
        self.assertEqual(effect.prot_length, 2211)
        self.assertEqual(effect.aa_change, None)

    def test_first_codon_ins_integenic_var(self):
        [effect] = VariantAnnotation.annotate_variant(self.gmDB, self.GA,
                                                      loc="1:3407092",
                                                      var="ins(A)")
        self.assertEqual(effect.gene, None)
        self.assertEqual(effect.transcript_id, None)
        self.assertEqual(effect.strand, None)
        self.assertEqual(effect.effect, "intergenic")
        self.assertEqual(effect.prot_pos, None)
        self.assertEqual(effect.prot_length, None)
        self.assertEqual(effect.aa_change, None)

    def test_first_codon_ins_noEnd_var(self):
        [effect] = VariantAnnotation.annotate_variant(self.gmDB, self.GA,
                                                      loc="1:3407093",
                                                      var="ins(A)")
        self.assertEqual(effect.gene, "MEGF6")
        self.assertEqual(effect.transcript_id, "NM_001409_1")
        self.assertEqual(effect.strand, "-")
        self.assertEqual(effect.effect, "noEnd")
        self.assertEqual(effect.prot_pos, 1542)
        self.assertEqual(effect.prot_length, 1542)
        self.assertEqual(effect.aa_change, None)

    def test_last_codon_ins_intergenic_var(self):
        [effect] = VariantAnnotation.annotate_variant(self.gmDB, self.GA,
                                                      loc="7:24727232",
                                                      var="ins(A)")
        self.assertEqual(effect.gene, None)
        self.assertEqual(effect.transcript_id, None)
        self.assertEqual(effect.strand, None)
        self.assertEqual(effect.effect, "intergenic")
        self.assertEqual(effect.prot_pos, None)
        self.assertEqual(effect.prot_length, None)
        self.assertEqual(effect.aa_change, None)

    def test_last_codon_ins_frameshift_var(self):
        [effect] = VariantAnnotation.annotate_variant(self.gmDB, self.GA,
                                                      loc="7:24727231",
                                                      var="ins(A)")
        self.assertEqual(effect.gene, "MPP6")
        self.assertEqual(effect.transcript_id, "NM_016447_1")
        self.assertEqual(effect.strand, "+")
        self.assertEqual(effect.effect, "frame-shift")
        self.assertEqual(effect.prot_pos, 541)
        self.assertEqual(effect.prot_length, 540)
        self.assertEqual(effect.aa_change, None)

    def test_first_codon_sub_noStart_var(self):
        [effect] = VariantAnnotation.annotate_variant(self.gmDB, self.GA,
                                                      loc="7:24663287",
                                                      var="sub(T->C)")
        self.assertEqual(effect.gene, "MPP6")
        self.assertEqual(effect.transcript_id, "NM_016447_1")
        self.assertEqual(effect.strand, "+")
        self.assertEqual(effect.effect, "noStart")
        self.assertEqual(effect.prot_pos, 1)
        self.assertEqual(effect.prot_length, 541)
        self.assertEqual(effect.aa_change, None)

    def test_last_codon_sub_noStop_var(self):
        [effect] = VariantAnnotation.annotate_variant(self.gmDB, self.GA,
                                                      loc="7:24727231",
                                                      var="sub(T->C)")
        self.assertEqual(effect.gene, "MPP6")
        self.assertEqual(effect.transcript_id, "NM_016447_1")
        self.assertEqual(effect.strand, "+")
        self.assertEqual(effect.effect, "noEnd")
        self.assertEqual(effect.prot_pos, 541)
        self.assertEqual(effect.prot_length, 541)
        self.assertEqual(effect.aa_change, None)

    def test_chr1_71418630_sub_var(self):
        effects = VariantAnnotation.annotate_variant(self.gmDB, self.GA,
                                                     loc="1:71418630",
                                                     var="sub(A->G)")
        self.assertEqual(len(effects), 8)
        effects_sorted = sorted(effects, key=lambda k: k.transcript_id)

        self.assertEqual(effects_sorted[0].gene, "PTGER3")
        self.assertEqual(effects_sorted[0].transcript_id, "NM_001126044_1")
        self.assertEqual(effects_sorted[0].strand, "-")
        self.assertEqual(effects_sorted[0].effect, "3'UTR")
        self.assertEqual(effects_sorted[0].prot_pos, None)
        self.assertEqual(effects_sorted[0].prot_length, None)
        self.assertEqual(effects_sorted[0].aa_change, None)

        self.assertEqual(effects_sorted[1].gene, "PTGER3")
        self.assertEqual(effects_sorted[1].transcript_id, "NM_198714_1")
        self.assertEqual(effects_sorted[1].strand, "-")
        self.assertEqual(effects_sorted[1].effect, "3'UTR-intron")
        self.assertEqual(effects_sorted[1].prot_pos, None)
        self.assertEqual(effects_sorted[1].prot_length, None)
        self.assertEqual(effects_sorted[1].aa_change, None)

        self.assertEqual(effects_sorted[2].gene, "PTGER3")
        self.assertEqual(effects_sorted[2].transcript_id, "NM_198716_1")
        self.assertEqual(effects_sorted[2].strand, "-")
        self.assertEqual(effects_sorted[2].effect, "intron")
        self.assertEqual(effects_sorted[2].prot_pos, 369)
        self.assertEqual(effects_sorted[2].prot_length, 375)
        self.assertEqual(effects_sorted[2].aa_change, None)

        self.assertEqual(effects_sorted[3].gene, "PTGER3")
        self.assertEqual(effects_sorted[3].transcript_id, "NM_198717_1")
        self.assertEqual(effects_sorted[3].strand, "-")
        self.assertEqual(effects_sorted[3].effect, "intron")
        self.assertEqual(effects_sorted[3].prot_pos, 360)
        self.assertEqual(effects_sorted[3].prot_length, 366)
        self.assertEqual(effects_sorted[3].aa_change, None)

        self.assertEqual(effects_sorted[4].gene, "PTGER3")
        self.assertEqual(effects_sorted[4].transcript_id, "NM_198718_1")
        self.assertEqual(effects_sorted[4].strand, "-")
        self.assertEqual(effects_sorted[4].effect, "missense")
        self.assertEqual(effects_sorted[4].prot_pos, 406)
        self.assertEqual(effects_sorted[4].prot_length, 418)
        self.assertEqual(effects_sorted[4].aa_change, "Ile->Thr")

        self.assertEqual(effects_sorted[5].gene, "PTGER3")
        self.assertEqual(effects_sorted[5].transcript_id, "NR_028292_1")
        self.assertEqual(effects_sorted[5].strand, "-")
        self.assertEqual(effects_sorted[5].effect, "non-coding-intron")
        self.assertEqual(effects_sorted[5].prot_pos, None)
        self.assertEqual(effects_sorted[5].prot_length, None)
        self.assertEqual(effects_sorted[5].aa_change, None)

        self.assertEqual(effects_sorted[6].gene, "PTGER3")
        self.assertEqual(effects_sorted[6].transcript_id, "NR_028293_1")
        self.assertEqual(effects_sorted[6].strand, "-")
        self.assertEqual(effects_sorted[6].effect, "non-coding-intron")
        self.assertEqual(effects_sorted[6].prot_pos, None)
        self.assertEqual(effects_sorted[6].prot_length, None)
        self.assertEqual(effects_sorted[6].aa_change, None)

        self.assertEqual(effects_sorted[7].gene, "PTGER3")
        self.assertEqual(effects_sorted[7].transcript_id, "NR_028294_1")
        self.assertEqual(effects_sorted[7].strand, "-")
        self.assertEqual(effects_sorted[7].effect, "non-coding-intron")
        self.assertEqual(effects_sorted[7].prot_pos, None)
        self.assertEqual(effects_sorted[7].prot_length, None)
        self.assertEqual(effects_sorted[7].aa_change, None)

    def test_chr20_56284593_ins_var(self):
        effects = VariantAnnotation.annotate_variant(self.gmDB, self.GA,
                                                     loc="20:56284593",
                                                     var="ins(CGGCGG)")
        self.assertEqual(len(effects), 4)
        effects_sorted = sorted(effects, key=lambda k: k.transcript_id)

        self.assertEqual(effects_sorted[0].gene, "PMEPA1")
        self.assertEqual(effects_sorted[0].transcript_id, "NM_020182_1")
        self.assertEqual(effects_sorted[0].strand, "-")
        self.assertEqual(effects_sorted[0].effect, "no-frame-shift")
        self.assertEqual(effects_sorted[0].prot_pos, 16)
        self.assertEqual(effects_sorted[0].prot_length, 287)
        self.assertEqual(effects_sorted[0].aa_change, None)

        self.assertEqual(effects_sorted[1].gene, "PMEPA1")
        self.assertEqual(effects_sorted[1].transcript_id, "NM_199169_1")
        self.assertEqual(effects_sorted[1].strand, "-")
        self.assertEqual(effects_sorted[1].effect, "intron")
        self.assertEqual(effects_sorted[1].prot_pos, 2)
        self.assertEqual(effects_sorted[1].prot_length, 253)
        self.assertEqual(effects_sorted[1].aa_change, None)

        self.assertEqual(effects_sorted[2].gene, "PMEPA1")
        self.assertEqual(effects_sorted[2].transcript_id, "NM_199170_1")
        self.assertEqual(effects_sorted[2].strand, "-")
        self.assertEqual(effects_sorted[2].effect, "5'UTR-intron")
        self.assertEqual(effects_sorted[2].prot_pos, None)
        self.assertEqual(effects_sorted[2].prot_length, None)
        self.assertEqual(effects_sorted[2].aa_change, None)

        self.assertEqual(effects_sorted[3].gene, "PMEPA1")
        self.assertEqual(effects_sorted[3].transcript_id, "NM_199171_1")
        self.assertEqual(effects_sorted[3].strand, "-")
        self.assertEqual(effects_sorted[3].effect, "5'UTR-intron")
        self.assertEqual(effects_sorted[3].prot_pos, None)
        self.assertEqual(effects_sorted[3].prot_length, None)
        self.assertEqual(effects_sorted[3].aa_change, None)

    def test_chr20_57478739_sub_var(self):
        effects = VariantAnnotation.annotate_variant(self.gmDB, self.GA,
                                                     loc="20:57478739",
                                                     var="sub(G->A)")
        self.assertEqual(len(effects), 8)
        effects_sorted = sorted(effects, key=lambda k: k.transcript_id)

        self.assertEqual(effects_sorted[0].gene, "GNAS")
        self.assertEqual(effects_sorted[0].transcript_id, "NM_000516_1")
        self.assertEqual(effects_sorted[0].strand, "+")
        self.assertEqual(effects_sorted[0].effect, "missense")
        self.assertEqual(effects_sorted[0].prot_pos, 109)
        self.assertEqual(effects_sorted[0].prot_length, 394)
        self.assertEqual(effects_sorted[0].aa_change, "Ala->Thr")

        self.assertEqual(effects_sorted[1].gene, "GNAS")
        self.assertEqual(effects_sorted[1].transcript_id, "NM_001077488_1")
        self.assertEqual(effects_sorted[1].strand, "+")
        self.assertEqual(effects_sorted[1].effect, "missense")
        self.assertEqual(effects_sorted[1].prot_pos, 110)
        self.assertEqual(effects_sorted[1].prot_length, 395)
        self.assertEqual(effects_sorted[1].aa_change, "Ala->Thr")

        self.assertEqual(effects_sorted[2].gene, "GNAS")
        self.assertEqual(effects_sorted[2].transcript_id, "NM_001077489_1")
        self.assertEqual(effects_sorted[2].strand, "+")
        self.assertEqual(effects_sorted[2].effect, "missense")
        self.assertEqual(effects_sorted[2].prot_pos, 94)
        self.assertEqual(effects_sorted[2].prot_length, 379)
        self.assertEqual(effects_sorted[2].aa_change, "Ala->Thr")

        self.assertEqual(effects_sorted[3].gene, "GNAS")
        self.assertEqual(effects_sorted[3].transcript_id, "NM_001077490_1")
        self.assertEqual(effects_sorted[3].strand, "+")
        self.assertEqual(effects_sorted[3].effect, "3'UTR")
        self.assertEqual(effects_sorted[3].prot_pos, None)
        self.assertEqual(effects_sorted[3].prot_length, None)
        self.assertEqual(effects_sorted[3].aa_change, None)

        self.assertEqual(effects_sorted[4].gene, "GNAS")
        self.assertEqual(effects_sorted[4].transcript_id, "NM_016592_1")
        self.assertEqual(effects_sorted[4].strand, "+")
        self.assertEqual(effects_sorted[4].effect, "3'UTR")
        self.assertEqual(effects_sorted[4].prot_pos, None)
        self.assertEqual(effects_sorted[4].prot_length, None)
        self.assertEqual(effects_sorted[4].aa_change, None)

        self.assertEqual(effects_sorted[5].gene, "GNAS")
        self.assertEqual(effects_sorted[5].transcript_id, "NM_080425_1")
        self.assertEqual(effects_sorted[5].strand, "+")
        self.assertEqual(effects_sorted[5].effect, "missense")
        self.assertEqual(effects_sorted[5].prot_pos, 752)
        self.assertEqual(effects_sorted[5].prot_length, 1037)
        self.assertEqual(effects_sorted[5].aa_change, "Ala->Thr")

        self.assertEqual(effects_sorted[6].gene, "GNAS")
        self.assertEqual(effects_sorted[6].transcript_id, "NM_080426_1")
        self.assertEqual(effects_sorted[6].strand, "+")
        self.assertEqual(effects_sorted[6].effect, "missense")
        self.assertEqual(effects_sorted[6].prot_pos, 95)
        self.assertEqual(effects_sorted[6].prot_length, 380)
        self.assertEqual(effects_sorted[6].aa_change, "Ala->Thr")

        self.assertEqual(effects_sorted[7].gene, "GNAS")
        self.assertEqual(effects_sorted[7].transcript_id, "NR_003259_1")
        self.assertEqual(effects_sorted[7].strand, "+")
        self.assertEqual(effects_sorted[7].effect, "non-coding")
        self.assertEqual(effects_sorted[7].prot_pos, None)
        self.assertEqual(effects_sorted[7].prot_length, None)
        self.assertEqual(effects_sorted[7].aa_change, None)

    def test_chr14_78227471_del_var(self):
        effects = VariantAnnotation.annotate_variant(self.gmDB, self.GA,
                                                     loc="14:78227471",
                                                     var="del(9)")
        self.assertEqual(len(effects), 3)
        effects_sorted = sorted(effects, key=lambda k: k.transcript_id)

        self.assertEqual(effects_sorted[0].gene, "C14orf178")
        self.assertEqual(effects_sorted[0].transcript_id, "NM_001173978_1")
        self.assertEqual(effects_sorted[0].strand, "+")
        self.assertEqual(effects_sorted[0].effect, "5'UTR-intron")
        self.assertEqual(effects_sorted[0].prot_pos, None)
        self.assertEqual(effects_sorted[0].prot_length, None)
        self.assertEqual(effects_sorted[0].aa_change, None)

        self.assertEqual(effects_sorted[1].gene, "SNW1")
        self.assertEqual(effects_sorted[1].transcript_id, "NM_012245_1")
        self.assertEqual(effects_sorted[1].strand, "-")
        self.assertEqual(effects_sorted[1].effect, "5'UTR")
        self.assertEqual(effects_sorted[1].prot_pos, None)
        self.assertEqual(effects_sorted[1].prot_length, None)
        self.assertEqual(effects_sorted[1].aa_change, None)

        self.assertEqual(effects_sorted[2].gene, "C14orf178")
        self.assertEqual(effects_sorted[2].transcript_id, "NM_174943_1")
        self.assertEqual(effects_sorted[2].strand, "+")
        self.assertEqual(effects_sorted[2].effect, "intron")
        self.assertEqual(effects_sorted[2].prot_pos, 25)
        self.assertEqual(effects_sorted[2].prot_length, 123)
        self.assertEqual(effects_sorted[2].aa_change, None)

    def test_chr3_128813981_sub_var(self):
        effects = VariantAnnotation.annotate_variant(self.gmDB, self.GA,
                                                     loc="3:128813981",
                                                     var="sub(C->T)")
        self.assertEqual(len(effects), 8)
        effects_sorted = sorted(effects, key=lambda k: k.transcript_id)

        self.assertEqual(effects_sorted[0].gene, "RAB43")
        self.assertEqual(effects_sorted[0].transcript_id, "NM_001204883_1")
        self.assertEqual(effects_sorted[0].strand, "-")
        self.assertEqual(effects_sorted[0].effect, "missense")
        self.assertEqual(effects_sorted[0].prot_pos, 79)
        self.assertEqual(effects_sorted[0].prot_length, 212)
        self.assertEqual(effects_sorted[0].aa_change, "Arg->Gln")

        self.assertEqual(effects_sorted[1].gene, "RAB43")
        self.assertEqual(effects_sorted[1].transcript_id, "NM_001204884_1")
        self.assertEqual(effects_sorted[1].strand, "-")
        self.assertEqual(effects_sorted[1].effect, "missense")
        self.assertEqual(effects_sorted[1].prot_pos, 79)
        self.assertEqual(effects_sorted[1].prot_length, 212)
        self.assertEqual(effects_sorted[1].aa_change, "Arg->Gln")

        self.assertEqual(effects_sorted[2].gene, "RAB43")
        self.assertEqual(effects_sorted[2].transcript_id, "NM_001204885_1")
        self.assertEqual(effects_sorted[2].strand, "-")
        self.assertEqual(effects_sorted[2].effect, "missense")
        self.assertEqual(effects_sorted[2].prot_pos, 79)
        self.assertEqual(effects_sorted[2].prot_length, 212)
        self.assertEqual(effects_sorted[2].aa_change, "Arg->Gln")

        self.assertEqual(effects_sorted[3].gene, "RAB43")
        self.assertEqual(effects_sorted[3].transcript_id, "NM_001204886_1")
        self.assertEqual(effects_sorted[3].strand, "-")
        self.assertEqual(effects_sorted[3].effect, "missense")
        self.assertEqual(effects_sorted[3].prot_pos, 79)
        self.assertEqual(effects_sorted[3].prot_length, 212)
        self.assertEqual(effects_sorted[3].aa_change, "Arg->Gln")

        self.assertEqual(effects_sorted[4].gene, "RAB43")
        self.assertEqual(effects_sorted[4].transcript_id, "NM_001204887_1")
        self.assertEqual(effects_sorted[4].strand, "-")
        self.assertEqual(effects_sorted[4].effect, "missense")
        self.assertEqual(effects_sorted[4].prot_pos, 79)
        self.assertEqual(effects_sorted[4].prot_length, 155)
        self.assertEqual(effects_sorted[4].aa_change, "Arg->Gln")

        self.assertEqual(effects_sorted[5].gene, "RAB43")
        self.assertEqual(effects_sorted[5].transcript_id, "NM_001204888_1")
        self.assertEqual(effects_sorted[5].strand, "-")
        self.assertEqual(effects_sorted[5].effect, "synonymous")
        self.assertEqual(effects_sorted[5].prot_pos, 74)
        self.assertEqual(effects_sorted[5].prot_length, 108)
        self.assertEqual(effects_sorted[5].aa_change, "Ala->Ala")

        self.assertEqual(effects_sorted[6].gene, "ISY1-RAB43")
        self.assertEqual(effects_sorted[6].transcript_id, "NM_001204890_1")
        self.assertEqual(effects_sorted[6].strand, "-")
        self.assertEqual(effects_sorted[6].effect, "missense")
        self.assertEqual(effects_sorted[6].prot_pos, 295)
        self.assertEqual(effects_sorted[6].prot_length, 331)
        self.assertEqual(effects_sorted[6].aa_change, "Gly->Ser")

        self.assertEqual(effects_sorted[7].gene, "RAB43")
        self.assertEqual(effects_sorted[7].transcript_id, "NM_198490_1")
        self.assertEqual(effects_sorted[7].strand, "-")
        self.assertEqual(effects_sorted[7].effect, "missense")
        self.assertEqual(effects_sorted[7].prot_pos, 79)
        self.assertEqual(effects_sorted[7].prot_length, 212)
        self.assertEqual(effects_sorted[7].aa_change, "Arg->Gln")

    def test_chr14_21895990_del_var(self):
        effects = VariantAnnotation.annotate_variant(self.gmDB, self.GA,
                                                     loc="14:21895990",
                                                     var="del(47)")
        self.assertEqual(len(effects), 2)
        effects_sorted = sorted(effects, key=lambda k: k.transcript_id)

        self.assertEqual(effects_sorted[0].gene, "CHD8")
        self.assertEqual(effects_sorted[0].transcript_id, "NM_001170629_1")
        self.assertEqual(effects_sorted[0].strand, "-")
        self.assertEqual(effects_sorted[0].effect, "splice-site")
        self.assertEqual(effects_sorted[0].prot_pos, 534)
        self.assertEqual(effects_sorted[0].prot_length, 2582)
        self.assertEqual(effects_sorted[0].aa_change, None)

        self.assertEqual(effects_sorted[1].gene, "CHD8")
        self.assertEqual(effects_sorted[1].transcript_id, "NM_020920_1")
        self.assertEqual(effects_sorted[1].strand, "-")
        self.assertEqual(effects_sorted[1].effect, "splice-site")
        self.assertEqual(effects_sorted[1].prot_pos, 255)
        self.assertEqual(effects_sorted[1].prot_length, 2303)
        self.assertEqual(effects_sorted[1].aa_change, None)

    def test_chr1_12175787_sub_var(self):
        effects = VariantAnnotation.annotate_variant(self.gmDB, self.GA,
                                                     loc="1:12175787",
                                                     var="sub(G->A)")
        self.assertEqual(len(effects), 2)
        effects_sorted = sorted(effects, key=lambda k: k.transcript_id)

        self.assertEqual(effects_sorted[0].gene, "TNFRSF8")
        self.assertEqual(effects_sorted[0].transcript_id, "NM_001243_1")
        self.assertEqual(effects_sorted[0].strand, "+")
        self.assertEqual(effects_sorted[0].effect, "splice-site")
        self.assertEqual(effects_sorted[0].prot_pos, 316)
        self.assertEqual(effects_sorted[0].prot_length, 596)
        self.assertEqual(effects_sorted[0].aa_change, None)

        self.assertEqual(effects_sorted[1].gene, "TNFRSF8")
        self.assertEqual(effects_sorted[1].transcript_id, "NM_001281430_1")
        self.assertEqual(effects_sorted[1].strand, "+")
        self.assertEqual(effects_sorted[1].effect, "splice-site")
        self.assertEqual(effects_sorted[1].prot_pos, 205)
        self.assertEqual(effects_sorted[1].prot_length, 484)
        self.assertEqual(effects_sorted[1].aa_change, None)

    def test_chr13_23904276_sub_var(self):
        effects = VariantAnnotation.annotate_variant(self.gmDB, self.GA,
                                                     loc="13:23904276",
                                                     var="sub(C->T)")
        self.assertEqual(len(effects), 2)
        effects_sorted = sorted(effects, key=lambda k: k.transcript_id)

        self.assertEqual(effects_sorted[0].gene, "SACS")
        self.assertEqual(effects_sorted[0].transcript_id, "NM_001278055_1")
        self.assertEqual(effects_sorted[0].strand, "-")
        self.assertEqual(effects_sorted[0].effect, "synonymous")
        self.assertEqual(effects_sorted[0].prot_pos, 4433)
        self.assertEqual(effects_sorted[0].prot_length, 4433)
        self.assertEqual(effects_sorted[0].aa_change, "End->End")

        self.assertEqual(effects_sorted[1].gene, "SACS")
        self.assertEqual(effects_sorted[1].transcript_id, "NM_014363_1")
        self.assertEqual(effects_sorted[1].strand, "-")
        self.assertEqual(effects_sorted[1].effect, "synonymous")
        self.assertEqual(effects_sorted[1].prot_pos, 4580)
        self.assertEqual(effects_sorted[1].prot_length, 4580)
        self.assertEqual(effects_sorted[1].aa_change, "End->End")

    def test_chr20_61476990_del_var(self):
        effects = VariantAnnotation.annotate_variant(self.gmDB, self.GA,
                                                     loc="20:61476990",
                                                     var="del(3)")
        self.assertEqual(len(effects), 2)
        effects_sorted = sorted(effects, key=lambda k: k.transcript_id)

        self.assertEqual(effects_sorted[0].gene, "TCFL5")
        self.assertEqual(effects_sorted[0].transcript_id, "NM_006602_1")
        self.assertEqual(effects_sorted[0].strand, "-")
        self.assertEqual(effects_sorted[0].effect, "intron")
        self.assertEqual(effects_sorted[0].prot_pos, 461)
        self.assertEqual(effects_sorted[0].prot_length, 501)
        self.assertEqual(effects_sorted[0].aa_change, None)

        self.assertEqual(effects_sorted[1].gene, "DPH3P1")
        self.assertEqual(effects_sorted[1].transcript_id, "NM_080750_1")
        self.assertEqual(effects_sorted[1].strand, "+")
        self.assertEqual(effects_sorted[1].effect, "5'UTR")
        self.assertEqual(effects_sorted[1].prot_pos, None)
        self.assertEqual(effects_sorted[1].prot_length, None)
        self.assertEqual(effects_sorted[1].aa_change, None)

    def test_chr3_56627768_del_var(self):
        effects = VariantAnnotation.annotate_variant(self.gmDB, self.GA,
                                                     loc="3:56627768",
                                                     var="del(4)")
        self.assertEqual(len(effects), 3)
        effects_sorted = sorted(effects, key=lambda k: k.transcript_id)

        self.assertEqual(effects_sorted[0].gene, "CCDC66")
        self.assertEqual(effects_sorted[0].transcript_id, "NM_001012506_1")
        self.assertEqual(effects_sorted[0].strand, "+")
        self.assertEqual(effects_sorted[0].effect, "frame-shift")
        self.assertEqual(effects_sorted[0].prot_pos, 406)
        self.assertEqual(effects_sorted[0].prot_length, 914)
        self.assertEqual(effects_sorted[0].aa_change, None)

        self.assertEqual(effects_sorted[1].gene, "CCDC66")
        self.assertEqual(effects_sorted[1].transcript_id, "NM_001141947_1")
        self.assertEqual(effects_sorted[1].strand, "+")
        self.assertEqual(effects_sorted[1].effect, "frame-shift")
        self.assertEqual(effects_sorted[1].prot_pos, 440)
        self.assertEqual(effects_sorted[1].prot_length, 948)
        self.assertEqual(effects_sorted[1].aa_change, None)

        self.assertEqual(effects_sorted[2].gene, "CCDC66")
        self.assertEqual(effects_sorted[2].transcript_id, "NR_024460_1")
        self.assertEqual(effects_sorted[2].strand, "+")
        self.assertEqual(effects_sorted[2].effect, "non-coding")
        self.assertEqual(effects_sorted[2].prot_pos, None)
        self.assertEqual(effects_sorted[2].prot_length, None)
        self.assertEqual(effects_sorted[2].aa_change, None)

    def test_chr17_43227526_ins_var(self):
        [effect] = VariantAnnotation.annotate_variant(self.gmDB, self.GA,
                                                      loc="17:43227526",
                                                      var="ins(GGAGCT)")

        self.assertEqual(effect.gene, "HEXIM1")
        self.assertEqual(effect.transcript_id, "NM_006460_1")
        self.assertEqual(effect.strand, "+")
        self.assertEqual(effect.effect, "no-frame-shift")
        self.assertEqual(effect.prot_pos, 323)
        self.assertEqual(effect.prot_length, 359)
        self.assertEqual(effect.aa_change, None)

    def test_chr5_56527122_sub_var(self):
        effects = VariantAnnotation.annotate_variant(self.gmDB, self.GA,
                                                     loc="5:56527122",
                                                     var="sub(C->T)")
        self.assertEqual(len(effects), 4)
        effects_sorted = sorted(effects, key=lambda k: k.transcript_id)

        self.assertEqual(effects_sorted[0].gene, "GPBP1")
        self.assertEqual(effects_sorted[0].transcript_id, "NM_001127235_1")
        self.assertEqual(effects_sorted[0].strand, "+")
        self.assertEqual(effects_sorted[0].effect, "missense")
        self.assertEqual(effects_sorted[0].prot_pos, 136)
        self.assertEqual(effects_sorted[0].prot_length, 465)
        self.assertEqual(effects_sorted[0].aa_change, "Arg->Cys")

        self.assertEqual(effects_sorted[1].gene, "GPBP1")
        self.assertEqual(effects_sorted[1].transcript_id, "NM_001127236_1")
        self.assertEqual(effects_sorted[1].strand, "+")
        self.assertEqual(effects_sorted[1].effect, "missense")
        self.assertEqual(effects_sorted[1].prot_pos, 136)
        self.assertEqual(effects_sorted[1].prot_length, 480)
        self.assertEqual(effects_sorted[1].aa_change, "Arg->Cys")

        self.assertEqual(effects_sorted[2].gene, "GPBP1")
        self.assertEqual(effects_sorted[2].transcript_id, "NM_001203246_1")
        self.assertEqual(effects_sorted[2].strand, "+")
        self.assertEqual(effects_sorted[2].effect, "5'UTR")
        self.assertEqual(effects_sorted[2].prot_pos, None)
        self.assertEqual(effects_sorted[2].prot_length, None)
        self.assertEqual(effects_sorted[2].aa_change, None)

        self.assertEqual(effects_sorted[3].gene, "GPBP1")
        self.assertEqual(effects_sorted[3].transcript_id, "NM_022913_1")
        self.assertEqual(effects_sorted[3].strand, "+")
        self.assertEqual(effects_sorted[3].effect, "missense")
        self.assertEqual(effects_sorted[3].prot_pos, 129)
        self.assertEqual(effects_sorted[3].prot_length, 473)
        self.assertEqual(effects_sorted[3].aa_change, "Arg->Cys")

    def test_chr3_97611838_del_var(self):
        [effect] = VariantAnnotation.annotate_variant(self.gmDB, self.GA,
                                                      loc="3:97611838",
                                                      var="del(4)")

        self.assertEqual(effect.gene, "CRYBG3")
        self.assertEqual(effect.transcript_id, "NM_153605_1")
        self.assertEqual(effect.strand, "+")
        self.assertEqual(effect.effect, "intron")
        self.assertEqual(effect.prot_pos, 2525)
        self.assertEqual(effect.prot_length, 2971)
        self.assertEqual(effect.aa_change, None)

    def test_chr4_2514166_del_var(self):
        effects = VariantAnnotation.annotate_variant(self.gmDB, self.GA,
                                                     loc="4:2514166",
                                                     var="del(3)")
        self.assertEqual(len(effects), 3)
        effects_sorted = sorted(effects, key=lambda k: k.transcript_id)

        self.assertEqual(effects_sorted[0].gene, "RNF4")
        self.assertEqual(effects_sorted[0].transcript_id, "NM_001185009_1")
        self.assertEqual(effects_sorted[0].strand, "+")
        self.assertEqual(effects_sorted[0].effect, "no-frame-shift")
        self.assertEqual(effects_sorted[0].prot_pos, 72)
        self.assertEqual(effects_sorted[0].prot_length, 190)
        self.assertEqual(effects_sorted[0].aa_change, None)

        self.assertEqual(effects_sorted[1].gene, "RNF4")
        self.assertEqual(effects_sorted[1].transcript_id, "NM_001185010_1")
        self.assertEqual(effects_sorted[1].strand, "+")
        self.assertEqual(effects_sorted[1].effect, "intron")
        self.assertEqual(effects_sorted[1].prot_pos, 72)
        self.assertEqual(effects_sorted[1].prot_length, 114)
        self.assertEqual(effects_sorted[1].aa_change, None)

        self.assertEqual(effects_sorted[2].gene, "RNF4")
        self.assertEqual(effects_sorted[2].transcript_id, "NM_002938_1")
        self.assertEqual(effects_sorted[2].strand, "+")
        self.assertEqual(effects_sorted[2].effect, "no-frame-shift")
        self.assertEqual(effects_sorted[2].prot_pos, 72)
        self.assertEqual(effects_sorted[2].prot_length, 190)
        self.assertEqual(effects_sorted[2].aa_change, None)

    def test_chr7_131870222_sub_var(self):
        [effect] = VariantAnnotation.annotate_variant(self.gmDB, self.GA,
                                                      loc="7:131870222",
                                                      var="sub(C->A)")

        self.assertEqual(effect.gene, "PLXNA4")
        self.assertEqual(effect.transcript_id, "NM_020911_1")
        self.assertEqual(effect.strand, "-")
        self.assertEqual(effect.effect, "missense")
        self.assertEqual(effect.prot_pos, 998)
        self.assertEqual(effect.prot_length, 1894)
        self.assertEqual(effect.aa_change, "Arg->Ser")

    def test_chr6_107780195_sub_var(self):
        [effect] = VariantAnnotation.annotate_variant(self.gmDB, self.GA,
                                                      loc="6:107780195",
                                                      var="sub(T->A)")

        self.assertEqual(effect.gene, "PDSS2")
        self.assertEqual(effect.transcript_id, "NM_020381_1")
        self.assertEqual(effect.strand, "-")
        self.assertEqual(effect.effect, "missense")
        self.assertEqual(effect.prot_pos, 99)
        self.assertEqual(effect.prot_length, 399)
        self.assertEqual(effect.aa_change, "Arg->Trp")

    def test_chr15_80137554_ins_var(self):
        effects = VariantAnnotation.annotate_variant(self.gmDB, self.GA,
                                                     loc="15:80137554",
                                                     var="ins(A)")
        self.assertEqual(len(effects), 4)
        effects_sorted = sorted(effects, key=lambda k: k.transcript_id)

        self.assertEqual(effects_sorted[0].gene, "MTHFS")
        self.assertEqual(effects_sorted[0].transcript_id, "NM_001199758_1")
        self.assertEqual(effects_sorted[0].strand, "-")
        self.assertEqual(effects_sorted[0].effect, "noEnd")
        self.assertEqual(effects_sorted[0].prot_pos, 147)
        self.assertEqual(effects_sorted[0].prot_length, 147)
        self.assertEqual(effects_sorted[0].aa_change, None)

        self.assertEqual(effects_sorted[1].gene, "ST20-MTHFS")
        self.assertEqual(effects_sorted[1].transcript_id, "NM_001199760_1")
        self.assertEqual(effects_sorted[1].strand, "-")
        self.assertEqual(effects_sorted[1].effect, "noEnd")
        self.assertEqual(effects_sorted[1].prot_pos, 180)
        self.assertEqual(effects_sorted[1].prot_length, 180)
        self.assertEqual(effects_sorted[1].aa_change, None)

        self.assertEqual(effects_sorted[2].gene, "MTHFS")
        self.assertEqual(effects_sorted[2].transcript_id, "NM_006441_1")
        self.assertEqual(effects_sorted[2].strand, "-")
        self.assertEqual(effects_sorted[2].effect, "noEnd")
        self.assertEqual(effects_sorted[2].prot_pos, 204)
        self.assertEqual(effects_sorted[2].prot_length, 204)
        self.assertEqual(effects_sorted[2].aa_change, None)

        self.assertEqual(effects_sorted[3].gene, "MTHFS")
        self.assertEqual(effects_sorted[3].transcript_id, "NR_037654_1")
        self.assertEqual(effects_sorted[3].strand, "-")
        self.assertEqual(effects_sorted[3].effect, "non-coding")
        self.assertEqual(effects_sorted[3].prot_pos, None)
        self.assertEqual(effects_sorted[3].prot_length, None)
        self.assertEqual(effects_sorted[3].aa_change, None)

    def test_chr1_207793410_sub_var(self):
        effects = VariantAnnotation.annotate_variant(self.gmDB, self.GA,
                                                     loc="1:207793410",
                                                     var="sub(C->T)")
        self.assertEqual(len(effects), 2)
        effects_sorted = sorted(effects, key=lambda k: k.transcript_id)

        self.assertEqual(effects_sorted[0].gene, "CR1")
        self.assertEqual(effects_sorted[0].transcript_id, "NM_000573_1")
        self.assertEqual(effects_sorted[0].strand, "+")
        self.assertEqual(effects_sorted[0].effect, "missense")
        self.assertEqual(effects_sorted[0].prot_pos, 1968)
        self.assertEqual(effects_sorted[0].prot_length, 2039)
        self.assertEqual(effects_sorted[0].aa_change, "Arg->Cys")

        self.assertEqual(effects_sorted[1].gene, "CR1")
        self.assertEqual(effects_sorted[1].transcript_id, "NM_000651_1")
        self.assertEqual(effects_sorted[1].strand, "+")
        self.assertEqual(effects_sorted[1].effect, "missense")
        self.assertEqual(effects_sorted[1].prot_pos, 2418)
        self.assertEqual(effects_sorted[1].prot_length, 2489)
        self.assertEqual(effects_sorted[1].aa_change, "Arg->Cys")

    def test_chr3_49051816_sub_var(self):
        [effect] = VariantAnnotation.annotate_variant(self.gmDB, self.GA,
                                                      loc="3:49051816",
                                                      var="sub(G->A)")

        self.assertEqual(effect.gene, "WDR6")
        self.assertEqual(effect.transcript_id, "NM_018031_1")
        self.assertEqual(effect.strand, "+")
        self.assertEqual(effect.effect, "synonymous")
        self.assertEqual(effect.prot_pos, 919)
        self.assertEqual(effect.prot_length, 1151)
        self.assertEqual(effect.aa_change, "Arg->Arg")

    def test_chr5_79855195_del_var(self):
        [effect] = VariantAnnotation.annotate_variant(self.gmDB, self.GA,
                                                      loc="5:79855195",
                                                      var="del(6)")

        self.assertEqual(effect.gene, "ANKRD34B")
        self.assertEqual(effect.transcript_id, "NM_001004441_1")
        self.assertEqual(effect.strand, "-")
        self.assertEqual(effect.effect, "no-frame-shift")
        self.assertEqual(effect.prot_pos, 213)
        self.assertEqual(effect.prot_length, 514)
        self.assertEqual(effect.aa_change, None)

    def test_chr3_112997521_sub_var(self):
        [effect] = VariantAnnotation.annotate_variant(self.gmDB, self.GA,
                                                      loc="3:112997521",
                                                      var="sub(A->T)")

        self.assertEqual(effect.gene, "BOC")
        self.assertEqual(effect.transcript_id, "NM_033254_1")
        self.assertEqual(effect.strand, "+")
        self.assertEqual(effect.effect, "synonymous")
        self.assertEqual(effect.prot_pos, 568)
        self.assertEqual(effect.prot_length, 1114)
        self.assertEqual(effect.aa_change, "Gly->Gly")

    def test_chr2_169417831_sub_var(self):
        effects = VariantAnnotation.annotate_variant(self.gmDB, self.GA,
                                                     loc="2:169417831",
                                                     var="sub(A->G)")
        self.assertEqual(len(effects), 2)
        effects_sorted = sorted(effects, key=lambda k: k.transcript_id)

        self.assertEqual(effects_sorted[0].gene, "CERS6")
        self.assertEqual(effects_sorted[0].transcript_id, "NM_001256126_1")
        self.assertEqual(effects_sorted[0].strand, "+")
        self.assertEqual(effects_sorted[0].effect, "missense")
        self.assertEqual(effects_sorted[0].prot_pos, 136)
        self.assertEqual(effects_sorted[0].prot_length, 392)
        self.assertEqual(effects_sorted[0].aa_change, "Met->Val")

        self.assertEqual(effects_sorted[1].gene, "CERS6")
        self.assertEqual(effects_sorted[1].transcript_id, "NM_203463_1")
        self.assertEqual(effects_sorted[1].strand, "+")
        self.assertEqual(effects_sorted[1].effect, "missense")
        self.assertEqual(effects_sorted[1].prot_pos, 136)
        self.assertEqual(effects_sorted[1].prot_length, 384)
        self.assertEqual(effects_sorted[1].aa_change, "Met->Val")

    def test_chr2_170062840_sub_var(self):
        [effect] = VariantAnnotation.annotate_variant(self.gmDB, self.GA,
                                                      loc="2:170062840",
                                                      var="sub(C->T)")

        self.assertEqual(effect.gene, "LRP2")
        self.assertEqual(effect.transcript_id, "NM_004525_1")
        self.assertEqual(effect.strand, "-")
        self.assertEqual(effect.effect, "missense")
        self.assertEqual(effect.prot_pos, 2464)
        self.assertEqual(effect.prot_length, 4655)
        self.assertEqual(effect.aa_change, "Gly->Ser")

    def test_chr17_72954572_sub_var(self):
        [effect] = VariantAnnotation.annotate_variant(self.gmDB, self.GA,
                                                      loc="17:72954572",
                                                      var="sub(A->T)")

        self.assertEqual(effect.gene, "HID1")
        self.assertEqual(effect.transcript_id, "NM_030630_1")
        self.assertEqual(effect.strand, "-")
        self.assertEqual(effect.effect, "synonymous")
        self.assertEqual(effect.prot_pos, 414)
        self.assertEqual(effect.prot_length, 788)
        self.assertEqual(effect.aa_change, "Ser->Ser")

    def test_chr4_140640596_sub_var(self):
        effects = VariantAnnotation.annotate_variant(self.gmDB, self.GA,
                                                     loc="4:140640596",
                                                     var="sub(C->T)")
        self.assertEqual(len(effects), 3)
        effects_sorted = sorted(effects, key=lambda k: k.transcript_id)

        self.assertEqual(effects_sorted[0].gene, "MGST2")
        self.assertEqual(effects_sorted[0].transcript_id, "NM_001204366_1")
        self.assertEqual(effects_sorted[0].strand, "+")
        self.assertEqual(effects_sorted[0].effect, "3'UTR-intron")
        self.assertEqual(effects_sorted[0].prot_pos, None)
        self.assertEqual(effects_sorted[0].prot_length, None)
        self.assertEqual(effects_sorted[0].aa_change, None)

        self.assertEqual(effects_sorted[1].gene, "MGST2")
        self.assertEqual(effects_sorted[1].transcript_id, "NM_001204367_1")
        self.assertEqual(effects_sorted[1].strand, "+")
        self.assertEqual(effects_sorted[1].effect, "3'UTR-intron")
        self.assertEqual(effects_sorted[1].prot_pos, None)
        self.assertEqual(effects_sorted[1].prot_length, None)
        self.assertEqual(effects_sorted[1].aa_change, None)

        self.assertEqual(effects_sorted[2].gene, "MAML3")
        self.assertEqual(effects_sorted[2].transcript_id, "NM_018717_1")
        self.assertEqual(effects_sorted[2].strand, "-")
        self.assertEqual(effects_sorted[2].effect, "missense")
        self.assertEqual(effects_sorted[2].prot_pos, 1096)
        self.assertEqual(effects_sorted[2].prot_length, 1134)
        self.assertEqual(effects_sorted[2].aa_change, "Gly->Arg")

    def test_chr7_40134547_ins_var(self):
        effects = VariantAnnotation.annotate_variant(self.gmDB, self.GA,
                                                     loc="7:40134547",
                                                     var="ins(GGCAGA)")
        self.assertEqual(len(effects), 2)
        effects_sorted = sorted(effects, key=lambda k: k.transcript_id)

        self.assertEqual(effects_sorted[0].gene, "CDK13")
        self.assertEqual(effects_sorted[0].transcript_id, "NM_003718_1")
        self.assertEqual(effects_sorted[0].strand, "+")
        self.assertEqual(effects_sorted[0].effect, "no-frame-shift")
        self.assertEqual(effects_sorted[0].prot_pos, 1503)
        self.assertEqual(effects_sorted[0].prot_length, 1512)
        self.assertEqual(effects_sorted[0].aa_change, None)

        self.assertEqual(effects_sorted[1].gene, "CDK13")
        self.assertEqual(effects_sorted[1].transcript_id, "NM_031267_1")
        self.assertEqual(effects_sorted[1].strand, "+")
        self.assertEqual(effects_sorted[1].effect, "no-frame-shift")
        self.assertEqual(effects_sorted[1].prot_pos, 1443)
        self.assertEqual(effects_sorted[1].prot_length, 1452)
        self.assertEqual(effects_sorted[1].aa_change, None)

    def test_chr9_98279102_sub_var(self):
        effects = VariantAnnotation.annotate_variant(self.gmDB, self.GA,
                                                     loc="9:98279102",
                                                     var="sub(T->G)")
        self.assertEqual(len(effects), 2)
        effects_sorted = sorted(effects, key=lambda k: k.transcript_id)

        self.assertEqual(effects_sorted[0].gene, "PTCH1")
        self.assertEqual(effects_sorted[0].transcript_id, "NM_001083602_1")
        self.assertEqual(effects_sorted[0].strand, "-")
        self.assertEqual(effects_sorted[0].effect, "5'UTR")
        self.assertEqual(effects_sorted[0].prot_pos, None)
        self.assertEqual(effects_sorted[0].prot_length, None)
        self.assertEqual(effects_sorted[0].aa_change, None)

        self.assertEqual(effects_sorted[1].gene, "PTCH1")
        self.assertEqual(effects_sorted[1].transcript_id, "NM_001083603_1")
        self.assertEqual(effects_sorted[1].strand, "-")
        self.assertEqual(effects_sorted[1].effect, "noStart")
        self.assertEqual(effects_sorted[1].prot_pos, 1)
        self.assertEqual(effects_sorted[1].prot_length, 1447)
        self.assertEqual(effects_sorted[1].aa_change, None)

    def test_chr2_166535661_del_var(self):
        effects = VariantAnnotation.annotate_variant(self.gmDB, self.GA,
                                                     loc="2:166535661",
                                                     var="del(3)")
        self.assertEqual(len(effects), 2)
        effects_sorted = sorted(effects, key=lambda k: k.transcript_id)

        self.assertEqual(effects_sorted[0].gene, "CSRNP3")
        self.assertEqual(effects_sorted[0].transcript_id, "NM_001172173_1")
        self.assertEqual(effects_sorted[0].strand, "+")
        self.assertEqual(effects_sorted[0].effect, "no-frame-shift")
        self.assertEqual(effects_sorted[0].prot_pos, 386)
        self.assertEqual(effects_sorted[0].prot_length, 585)
        self.assertEqual(effects_sorted[0].aa_change, None)

        self.assertEqual(effects_sorted[1].gene, "CSRNP3")
        self.assertEqual(effects_sorted[1].transcript_id, "NM_024969_1")
        self.assertEqual(effects_sorted[1].strand, "+")
        self.assertEqual(effects_sorted[1].effect, "no-frame-shift")
        self.assertEqual(effects_sorted[1].prot_pos, 386)
        self.assertEqual(effects_sorted[1].prot_length, 585)
        self.assertEqual(effects_sorted[1].aa_change, None)

    def test_chr4_76734406_sub_var(self):
        [effect] = VariantAnnotation.annotate_variant(self.gmDB, self.GA,
                                                      loc="4:76734406",
                                                      var="sub(T->C)")

        self.assertEqual(effect.gene, "USO1")
        self.assertEqual(effect.transcript_id, "NM_003715_1")
        self.assertEqual(effect.strand, "+")
        self.assertEqual(effect.effect, "synonymous")
        self.assertEqual(effect.prot_pos, 899)
        self.assertEqual(effect.prot_length, 912)
        self.assertEqual(effect.aa_change, "Asp->Asp")

    def test_chr12_70824294_del_var(self):
        [effect] = VariantAnnotation.annotate_variant(self.gmDB, self.GA,
                                                      loc="12:70824294",
                                                      var="del(3)")

        self.assertEqual(effect.gene, "KCNMB4")
        self.assertEqual(effect.transcript_id, "NM_014505_1")
        self.assertEqual(effect.strand, "+")
        self.assertEqual(effect.effect, "no-frame-shift")
        self.assertEqual(effect.prot_pos, 165)
        self.assertEqual(effect.prot_length, 210)
        self.assertEqual(effect.aa_change, None)

    def test_chr20_34243229_sub_var(self):
        effects = VariantAnnotation.annotate_variant(self.gmDB, self.GA,
                                                     loc="20:34243229",
                                                     var="sub(G->A)")
        self.assertEqual(len(effects), 10)
        effects_sorted = sorted(effects, key=lambda k: k.transcript_id)

        self.assertEqual(effects_sorted[0].gene, "RBM12")
        self.assertEqual(effects_sorted[0].transcript_id, "NM_001198838_1")
        self.assertEqual(effects_sorted[0].strand, "-")
        self.assertEqual(effects_sorted[0].effect, "missense")
        self.assertEqual(effects_sorted[0].prot_pos, 6)
        self.assertEqual(effects_sorted[0].prot_length, 932)
        self.assertEqual(effects_sorted[0].aa_change, "Arg->Cys")

        self.assertEqual(effects_sorted[1].gene, "RBM12")
        self.assertEqual(effects_sorted[1].transcript_id, "NM_001198840_1")
        self.assertEqual(effects_sorted[1].strand, "-")
        self.assertEqual(effects_sorted[1].effect, "missense")
        self.assertEqual(effects_sorted[1].prot_pos, 6)
        self.assertEqual(effects_sorted[1].prot_length, 932)
        self.assertEqual(effects_sorted[1].aa_change, "Arg->Cys")

        self.assertEqual(effects_sorted[2].gene, "CPNE1")
        self.assertEqual(effects_sorted[2].transcript_id, "NM_001198863_1")
        self.assertEqual(effects_sorted[2].strand, "-")
        self.assertEqual(effects_sorted[2].effect, "5'UTR-intron")
        self.assertEqual(effects_sorted[2].prot_pos, None)
        self.assertEqual(effects_sorted[2].prot_length, None)
        self.assertEqual(effects_sorted[2].aa_change, None)

        self.assertEqual(effects_sorted[3].gene, "RBM12")
        self.assertEqual(effects_sorted[3].transcript_id, "NM_006047_1")
        self.assertEqual(effects_sorted[3].strand, "-")
        self.assertEqual(effects_sorted[3].effect, "missense")
        self.assertEqual(effects_sorted[3].prot_pos, 6)
        self.assertEqual(effects_sorted[3].prot_length, 932)
        self.assertEqual(effects_sorted[3].aa_change, "Arg->Cys")

        self.assertEqual(effects_sorted[4].gene, "RBM12")
        self.assertEqual(effects_sorted[4].transcript_id, "NM_152838_1")
        self.assertEqual(effects_sorted[4].strand, "-")
        self.assertEqual(effects_sorted[4].effect, "missense")
        self.assertEqual(effects_sorted[4].prot_pos, 6)
        self.assertEqual(effects_sorted[4].prot_length, 932)
        self.assertEqual(effects_sorted[4].aa_change, "Arg->Cys")

        self.assertEqual(effects_sorted[5].gene, "CPNE1")
        self.assertEqual(effects_sorted[5].transcript_id, "NM_152925_1")
        self.assertEqual(effects_sorted[5].strand, "-")
        self.assertEqual(effects_sorted[5].effect, "5'UTR-intron")
        self.assertEqual(effects_sorted[5].prot_pos, None)
        self.assertEqual(effects_sorted[5].prot_length, None)
        self.assertEqual(effects_sorted[5].aa_change, None)

        self.assertEqual(effects_sorted[6].gene, "CPNE1")
        self.assertEqual(effects_sorted[6].transcript_id, "NM_152926_1")
        self.assertEqual(effects_sorted[6].strand, "-")
        self.assertEqual(effects_sorted[6].effect, "5'UTR-intron")
        self.assertEqual(effects_sorted[6].prot_pos, None)
        self.assertEqual(effects_sorted[6].prot_length, None)
        self.assertEqual(effects_sorted[6].aa_change, None)

        self.assertEqual(effects_sorted[7].gene, "CPNE1")
        self.assertEqual(effects_sorted[7].transcript_id, "NM_152927_1")
        self.assertEqual(effects_sorted[7].strand, "-")
        self.assertEqual(effects_sorted[7].effect, "5'UTR-intron")
        self.assertEqual(effects_sorted[7].prot_pos, None)
        self.assertEqual(effects_sorted[7].prot_length, None)
        self.assertEqual(effects_sorted[7].aa_change, None)

        self.assertEqual(effects_sorted[8].gene, "CPNE1")
        self.assertEqual(effects_sorted[8].transcript_id, "NM_152928_1")
        self.assertEqual(effects_sorted[8].strand, "-")
        self.assertEqual(effects_sorted[8].effect, "5'UTR-intron")
        self.assertEqual(effects_sorted[8].prot_pos, None)
        self.assertEqual(effects_sorted[8].prot_length, None)
        self.assertEqual(effects_sorted[8].aa_change, None)

        self.assertEqual(effects_sorted[9].gene, "CPNE1")
        self.assertEqual(effects_sorted[9].transcript_id, "NR_037188_1")
        self.assertEqual(effects_sorted[9].strand, "-")
        self.assertEqual(effects_sorted[9].effect, "non-coding")
        self.assertEqual(effects_sorted[9].prot_pos, None)
        self.assertEqual(effects_sorted[9].prot_length, None)
        self.assertEqual(effects_sorted[9].aa_change, None)

    def test_chr7_6505720_del_var(self):
        effects = VariantAnnotation.annotate_variant(self.gmDB, self.GA,
                                                     loc="7:6505720",
                                                     var="del(3)")
        self.assertEqual(len(effects), 2)
        effects_sorted = sorted(effects, key=lambda k: k.transcript_id)

        self.assertEqual(effects_sorted[0].gene, "KDELR2")
        self.assertEqual(effects_sorted[0].transcript_id, "NM_001100603_1")
        self.assertEqual(effects_sorted[0].strand, "-")
        self.assertEqual(effects_sorted[0].effect, "intron")
        self.assertEqual(effects_sorted[0].prot_pos, 118)
        self.assertEqual(effects_sorted[0].prot_length, 187)
        self.assertEqual(effects_sorted[0].aa_change, None)

        self.assertEqual(effects_sorted[1].gene, "KDELR2")
        self.assertEqual(effects_sorted[1].transcript_id, "NM_006854_1")
        self.assertEqual(effects_sorted[1].strand, "-")
        self.assertEqual(effects_sorted[1].effect, "no-frame-shift")
        self.assertEqual(effects_sorted[1].prot_pos, 195)
        self.assertEqual(effects_sorted[1].prot_length, 212)
        self.assertEqual(effects_sorted[1].aa_change, None)

    def test_chr3_195966608_del_var(self):
        [effect] = VariantAnnotation.annotate_variant(self.gmDB, self.GA,
                                                      loc="3:195966608",
                                                      var="del(4)")

        self.assertEqual(effect.gene, "PCYT1A")
        self.assertEqual(effect.transcript_id, "NM_005017_1")
        self.assertEqual(effect.strand, "-")
        self.assertEqual(effect.effect, "intron")
        self.assertEqual(effect.prot_pos, 237)
        self.assertEqual(effect.prot_length, 368)
        self.assertEqual(effect.aa_change, None)

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
        self.assertEqual(effects_sorted[0].prot_pos, 693)
        self.assertEqual(effects_sorted[0].prot_length, 1212)
        self.assertEqual(effects_sorted[0].aa_change, None)

        self.assertEqual(effects_sorted[1].gene, "ANKFY1")
        self.assertEqual(effects_sorted[1].transcript_id, "NM_016376_1")
        self.assertEqual(effects_sorted[1].strand, "-")
        self.assertEqual(effects_sorted[1].effect, "splice-site")
        self.assertEqual(effects_sorted[1].prot_pos, 651)
        self.assertEqual(effects_sorted[1].prot_length, 1171)
        self.assertEqual(effects_sorted[1].aa_change, None)

        self.assertEqual(effects_sorted[2].gene, "ANKFY1")
        self.assertEqual(effects_sorted[2].transcript_id, "NR_047571_1")
        self.assertEqual(effects_sorted[2].strand, "-")
        self.assertEqual(effects_sorted[2].effect, "non-coding-intron")
        self.assertEqual(effects_sorted[2].prot_pos, None)
        self.assertEqual(effects_sorted[2].prot_length, None)
        self.assertEqual(effects_sorted[2].aa_change, None)

    def test_chr7_31609423_sub_var(self):
        effects = VariantAnnotation.annotate_variant(self.gmDB, self.GA,
                                                     loc="7:31609423",
                                                     var="sub(G->C)")
        self.assertEqual(len(effects), 4)
        effects_sorted = sorted(effects, key=lambda k: k.transcript_id)

        self.assertEqual(effects_sorted[0].gene, "CCDC129")
        self.assertEqual(effects_sorted[0].transcript_id, "NM_001257967_1")
        self.assertEqual(effects_sorted[0].strand, "+")
        self.assertEqual(effects_sorted[0].effect, "missense")
        self.assertEqual(effects_sorted[0].prot_pos, 113)
        self.assertEqual(effects_sorted[0].prot_length, 1054)
        self.assertEqual(effects_sorted[0].aa_change, "Arg->Thr")

        self.assertEqual(effects_sorted[1].gene, "CCDC129")
        self.assertEqual(effects_sorted[1].transcript_id, "NM_001257968_1")
        self.assertEqual(effects_sorted[1].strand, "+")
        self.assertEqual(effects_sorted[1].effect, "missense")
        self.assertEqual(effects_sorted[1].prot_pos, 129)
        self.assertEqual(effects_sorted[1].prot_length, 1062)
        self.assertEqual(effects_sorted[1].aa_change, "Arg->Thr")

        self.assertEqual(effects_sorted[2].gene, "CCDC129")
        self.assertEqual(effects_sorted[2].transcript_id, "NM_194300_1")
        self.assertEqual(effects_sorted[2].strand, "+")
        self.assertEqual(effects_sorted[2].effect, "missense")
        self.assertEqual(effects_sorted[2].prot_pos, 103)
        self.assertEqual(effects_sorted[2].prot_length, 1044)
        self.assertEqual(effects_sorted[2].aa_change, "Arg->Thr")

        self.assertEqual(effects_sorted[3].gene, "CCDC129")
        self.assertEqual(effects_sorted[3].transcript_id, "NR_047565_1")
        self.assertEqual(effects_sorted[3].strand, "+")
        self.assertEqual(effects_sorted[3].effect, "non-coding")
        self.assertEqual(effects_sorted[3].prot_pos, None)
        self.assertEqual(effects_sorted[3].prot_length, None)
        self.assertEqual(effects_sorted[3].aa_change, None)

    def test_chr3_136057284_ins_var(self):
        [effect] = VariantAnnotation.annotate_variant(self.gmDB, self.GA,
                                                      loc="3:136057284",
                                                      var="ins(TGA)")

        self.assertEqual(effect.gene, "STAG1")
        self.assertEqual(effect.transcript_id, "NM_005862_1")
        self.assertEqual(effect.strand, "-")
        self.assertEqual(effect.effect, "no-frame-shift")
        self.assertEqual(effect.prot_pos, 1227)
        self.assertEqual(effect.prot_length, 1258)
        self.assertEqual(effect.aa_change, None)

    def test_chr1_120311364_sub_var(self):
        effects = VariantAnnotation.annotate_variant(self.gmDB, self.GA,
                                                     loc="1:120311364",
                                                     var="sub(C->A)")
        self.assertEqual(len(effects), 2)
        effects_sorted = sorted(effects, key=lambda k: k.transcript_id)

        self.assertEqual(effects_sorted[0].gene, "HMGCS2")
        self.assertEqual(effects_sorted[0].transcript_id, "NM_001166107_1")
        self.assertEqual(effects_sorted[0].strand, "-")
        self.assertEqual(effects_sorted[0].effect, "missense")
        self.assertEqual(effects_sorted[0].prot_pos, 35)
        self.assertEqual(effects_sorted[0].prot_length, 466)
        self.assertEqual(effects_sorted[0].aa_change, "Arg->Met")

        self.assertEqual(effects_sorted[1].gene, "HMGCS2")
        self.assertEqual(effects_sorted[1].transcript_id, "NM_005518_1")
        self.assertEqual(effects_sorted[1].strand, "-")
        self.assertEqual(effects_sorted[1].effect, "missense")
        self.assertEqual(effects_sorted[1].prot_pos, 35)
        self.assertEqual(effects_sorted[1].prot_length, 508)
        self.assertEqual(effects_sorted[1].aa_change, "Arg->Met")

    def test_chr3_128969525_sub_var(self):
        [effect] = VariantAnnotation.annotate_variant(self.gmDB, self.GA,
                                                      loc="3:128969525",
                                                      var="sub(G->T)")

        self.assertEqual(effect.gene, "COPG1")
        self.assertEqual(effect.transcript_id, "NM_016128_1")
        self.assertEqual(effect.strand, "+")
        self.assertEqual(effect.effect, "missense")
        self.assertEqual(effect.prot_pos, 13)
        self.assertEqual(effect.prot_length, 874)
        self.assertEqual(effect.aa_change, "Gly->Val")

    def test_chr8_3046533_sub_var(self):
        [effect] = VariantAnnotation.annotate_variant(self.gmDB, self.GA,
                                                      loc="8:3046533",
                                                      var="sub(A->T)")

        self.assertEqual(effect.gene, "CSMD1")
        self.assertEqual(effect.transcript_id, "NM_033225_1")
        self.assertEqual(effect.strand, "-")
        self.assertEqual(effect.effect, "missense")
        self.assertEqual(effect.prot_pos, 1800)
        self.assertEqual(effect.prot_length, 3564)
        self.assertEqual(effect.aa_change, "Val->Glu")

    def test_chr12_93792633_ins_var(self):
        effects = VariantAnnotation.annotate_variant(self.gmDB, self.GA,
                                                     loc="12:93792633",
                                                     var="ins(T)")
        self.assertEqual(len(effects), 4)
        effects_sorted = sorted(effects, key=lambda k: k.transcript_id)

        self.assertEqual(effects_sorted[0].gene, "NUDT4")
        self.assertEqual(effects_sorted[0].transcript_id, "NM_019094_1")
        self.assertEqual(effects_sorted[0].strand, "+")
        self.assertEqual(effects_sorted[0].effect, "intron")
        self.assertEqual(effects_sorted[0].prot_pos, 114)
        self.assertEqual(effects_sorted[0].prot_length, 181)
        self.assertEqual(effects_sorted[0].aa_change, None)

        self.assertEqual(effects_sorted[1].gene, "NUDT4")
        self.assertEqual(effects_sorted[1].transcript_id, "NM_199040_1")
        self.assertEqual(effects_sorted[1].strand, "+")
        self.assertEqual(effects_sorted[1].effect, "intron")
        self.assertEqual(effects_sorted[1].prot_pos, 115)
        self.assertEqual(effects_sorted[1].prot_length, 182)
        self.assertEqual(effects_sorted[1].aa_change, None)

        self.assertEqual(effects_sorted[2].gene, "NUDT4P1")
        self.assertEqual(effects_sorted[2].transcript_id, "NR_002212_1")
        self.assertEqual(effects_sorted[2].strand, "+")
        self.assertEqual(effects_sorted[2].effect, "non-coding-intron")
        self.assertEqual(effects_sorted[2].prot_pos, None)
        self.assertEqual(effects_sorted[2].prot_length, None)
        self.assertEqual(effects_sorted[2].aa_change, None)

        self.assertEqual(effects_sorted[3].gene, "NUDT4P2")
        self.assertEqual(effects_sorted[3].transcript_id, "NR_104005_1")
        self.assertEqual(effects_sorted[3].strand, "+")
        self.assertEqual(effects_sorted[3].effect, "non-coding-intron")
        self.assertEqual(effects_sorted[3].prot_pos, None)
        self.assertEqual(effects_sorted[3].prot_length, None)
        self.assertEqual(effects_sorted[3].aa_change, None)

    def test_chr12_64841908_del_var(self):
        effects = VariantAnnotation.annotate_variant(self.gmDB, self.GA,
                                                     loc="12:64841908",
                                                     var="del(2)")
        self.assertEqual(len(effects), 2)
        effects_sorted = sorted(effects, key=lambda k: k.transcript_id)

        self.assertEqual(effects_sorted[0].gene, "XPOT")
        self.assertEqual(effects_sorted[0].transcript_id, "NM_007235_1")
        self.assertEqual(effects_sorted[0].strand, "+")
        self.assertEqual(effects_sorted[0].effect, "frame-shift")
        self.assertEqual(effects_sorted[0].prot_pos, 962)
        self.assertEqual(effects_sorted[0].prot_length, 962)
        self.assertEqual(effects_sorted[0].aa_change, None)

        self.assertEqual(effects_sorted[1].gene, "XPOT")
        self.assertEqual(effects_sorted[1].transcript_id, "NM_007235_1")
        self.assertEqual(effects_sorted[1].strand, "+")
        self.assertEqual(effects_sorted[1].effect, "frame-shift")
        self.assertEqual(effects_sorted[1].prot_pos, 962)
        self.assertEqual(effects_sorted[1].prot_length, 962)
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
        self.assertEqual(effects_sorted[0].effect, "splice-site")
        self.assertEqual(effects_sorted[0].prot_pos, 248)
        self.assertEqual(effects_sorted[0].prot_length, 262)
        self.assertEqual(effects_sorted[0].aa_change, None)

        self.assertEqual(effects_sorted[1].gene, "NEURL2")
        self.assertEqual(effects_sorted[1].transcript_id, "NM_080749_1")
        self.assertEqual(effects_sorted[1].strand, "-")
        self.assertEqual(effects_sorted[1].effect, "splice-site")
        self.assertEqual(effects_sorted[1].prot_pos, 248)
        self.assertEqual(effects_sorted[1].prot_length, 286)
        self.assertEqual(effects_sorted[1].aa_change, None)

    def test_chr1_802610_867930_CNV_var(self):
        effects = VariantAnnotation.annotate_variant(self.gmDB, self.GA,
                                                     loc="1:802610-867930",
                                                     var="CNV+")
        self.assertEqual(len(effects), 3)
        effects_sorted = sorted(effects, key=lambda k: k.transcript_id)

        self.assertEqual(effects_sorted[0].gene, "SAMD11")
        self.assertEqual(effects_sorted[0].transcript_id, "NM_152486_1")
        self.assertEqual(effects_sorted[0].strand, "+")
        self.assertEqual(effects_sorted[0].effect, "unknown")
        self.assertEqual(effects_sorted[0].prot_pos, None)
        self.assertEqual(effects_sorted[0].prot_length, None)
        self.assertEqual(effects_sorted[0].aa_change, None)

        self.assertEqual(effects_sorted[1].gene, "LOC100130417")
        self.assertEqual(effects_sorted[1].transcript_id, "NR_026874_1")
        self.assertEqual(effects_sorted[1].strand, "-")
        self.assertEqual(effects_sorted[1].effect, "unknown")
        self.assertEqual(effects_sorted[1].prot_pos, None)
        self.assertEqual(effects_sorted[1].prot_length, None)
        self.assertEqual(effects_sorted[1].aa_change, None)

        self.assertEqual(effects_sorted[2].gene, "FAM41C")
        self.assertEqual(effects_sorted[2].transcript_id, "NR_027055_1")
        self.assertEqual(effects_sorted[2].strand, "-")
        self.assertEqual(effects_sorted[2].effect, "unknown")
        self.assertEqual(effects_sorted[2].prot_pos, None)
        self.assertEqual(effects_sorted[2].prot_length, None)
        self.assertEqual(effects_sorted[2].aa_change, None)

    def test_chr4_41748269_ins_var(self):
        var = "ins(GCCGCGGCCGCTGCGGCT)"
        [effect] = VariantAnnotation.annotate_variant(self.gmDB, self.GA,
                                                      loc="4:41748269",
                                                      var=var)

        self.assertEqual(effect.gene, "PHOX2B")
        self.assertEqual(effect.transcript_id, "NM_003924_1")
        self.assertEqual(effect.strand, "-")
        self.assertEqual(effect.effect, "no-frame-shift")
        self.assertEqual(effect.prot_pos, 167)
        self.assertEqual(effect.prot_length, 314)
        self.assertEqual(effect.aa_change, None)

    def test_chr21_11097543_del_var(self):
        effects = VariantAnnotation.annotate_variant(self.gmDB, self.GA,
                                                     loc="21:11097543",
                                                     var="del(2)")
        self.assertEqual(len(effects), 5)
        effects_sorted = sorted(effects, key=lambda k: k.transcript_id)

        self.assertEqual(effects_sorted[0].gene, "BAGE")
        self.assertEqual(effects_sorted[0].transcript_id, "NM_001187_1")
        self.assertEqual(effects_sorted[0].strand, "-")
        self.assertEqual(effects_sorted[0].effect, "frame-shift")
        self.assertEqual(effects_sorted[0].prot_pos, 40)
        self.assertEqual(effects_sorted[0].prot_length, 39)
        self.assertEqual(effects_sorted[0].aa_change, None)

        self.assertEqual(effects_sorted[1].gene, "BAGE4")
        self.assertEqual(effects_sorted[1].transcript_id, "NM_181704_1")
        self.assertEqual(effects_sorted[1].strand, "-")
        self.assertEqual(effects_sorted[1].effect, "noEnd")
        self.assertEqual(effects_sorted[1].prot_pos, 40)
        self.assertEqual(effects_sorted[1].prot_length, 40)
        self.assertEqual(effects_sorted[1].aa_change, None)

        self.assertEqual(effects_sorted[2].gene, "BAGE3")
        self.assertEqual(effects_sorted[2].transcript_id, "NM_182481_1")
        self.assertEqual(effects_sorted[2].strand, "-")
        self.assertEqual(effects_sorted[2].effect, "splice-site")
        self.assertEqual(effects_sorted[2].prot_pos, 39)
        self.assertEqual(effects_sorted[2].prot_length, 110)
        self.assertEqual(effects_sorted[2].aa_change, None)

        self.assertEqual(effects_sorted[3].gene, "BAGE2")
        self.assertEqual(effects_sorted[3].transcript_id, "NM_182482_1")
        self.assertEqual(effects_sorted[3].strand, "-")
        self.assertEqual(effects_sorted[3].effect, "splice-site")
        self.assertEqual(effects_sorted[3].prot_pos, 39)
        self.assertEqual(effects_sorted[3].prot_length, 110)
        self.assertEqual(effects_sorted[3].aa_change, None)

        self.assertEqual(effects_sorted[4].gene, "BAGE5")
        self.assertEqual(effects_sorted[4].transcript_id, "NM_182484_1")
        self.assertEqual(effects_sorted[4].strand, "-")
        self.assertEqual(effects_sorted[4].effect, "frame-shift")
        self.assertEqual(effects_sorted[4].prot_pos, 40)
        self.assertEqual(effects_sorted[4].prot_length, 39)
        self.assertEqual(effects_sorted[4].aa_change, None)

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
        self.assertEqual(effects_sorted[0].prot_pos, 419)
        self.assertEqual(effects_sorted[0].prot_length, 1912)
        self.assertEqual(effects_sorted[0].aa_change, None)

        self.assertEqual(effects_sorted[1].gene, "AK9")
        self.assertEqual(effects_sorted[1].transcript_id, "NM_145025_1")
        self.assertEqual(effects_sorted[1].strand, "-")
        self.assertEqual(effects_sorted[1].effect, "noEnd")
        self.assertEqual(effects_sorted[1].prot_pos, 422)
        self.assertEqual(effects_sorted[1].prot_length, 422)
        self.assertEqual(effects_sorted[1].aa_change, None)

    def test_chr19_35249941_ins_var(self):
        [effect] = VariantAnnotation.annotate_variant(self.gmDB, self.GA,
                                                      loc="19:35249941",
                                                      var="ins(AA)")

        self.assertEqual(effect.gene, "ZNF599")
        self.assertEqual(effect.transcript_id, "NM_001007248_1")
        self.assertEqual(effect.strand, "-")
        self.assertEqual(effect.effect, "frame-shift")
        self.assertEqual(effect.prot_pos, 589)
        self.assertEqual(effect.prot_length, 588)
        self.assertEqual(effect.aa_change, None)

    def test_chr13_45911524_ins_var(self):
        var = "ins(ACATTTTTCCATTTCTAAACCAT)"
        [effect] = VariantAnnotation.annotate_variant(self.gmDB, self.GA,
                                                      loc="13:45911524",
                                                      var=var)

        self.assertEqual(effect.gene, "TPT1")
        self.assertEqual(effect.transcript_id, "NM_003295_1")
        self.assertEqual(effect.strand, "-")
        self.assertEqual(effect.effect, "splice-site")
        self.assertEqual(effect.prot_pos, 173)
        self.assertEqual(effect.prot_length, 173)
        self.assertEqual(effect.aa_change, None)

    def test_chr9_130422308_del_var(self):
        effects = VariantAnnotation.annotate_variant(self.gmDB, self.GA,
                                                     loc="9:130422308",
                                                     var="del(1)")
        self.assertEqual(len(effects), 2)
        effects_sorted = sorted(effects, key=lambda k: k.transcript_id)

        self.assertEqual(effects_sorted[0].gene, "STXBP1")
        self.assertEqual(effects_sorted[0].transcript_id, "NM_001032221_1")
        self.assertEqual(effects_sorted[0].strand, "+")
        self.assertEqual(effects_sorted[0].effect, "splice-site")
        self.assertEqual(effects_sorted[0].prot_pos, 82)
        self.assertEqual(effects_sorted[0].prot_length, 595)
        self.assertEqual(effects_sorted[0].aa_change, None)

        self.assertEqual(effects_sorted[1].gene, "STXBP1")
        self.assertEqual(effects_sorted[1].transcript_id, "NM_003165_1")
        self.assertEqual(effects_sorted[1].strand, "+")
        self.assertEqual(effects_sorted[1].effect, "splice-site")
        self.assertEqual(effects_sorted[1].prot_pos, 82)
        self.assertEqual(effects_sorted[1].prot_length, 604)
        self.assertEqual(effects_sorted[1].aa_change, None)

    def test_chr6_99817476_del_var(self):
        [effect] = VariantAnnotation.annotate_variant(self.gmDB, self.GA,
                                                      loc="6:99817476",
                                                      var="del(22)")

        self.assertEqual(effect.gene, "COQ3")
        self.assertEqual(effect.transcript_id, "NM_017421_1")
        self.assertEqual(effect.strand, "-")
        self.assertEqual(effect.effect, "frame-shift")
        self.assertEqual(effect.prot_pos, 363)
        self.assertEqual(effect.prot_length, 369)
        self.assertEqual(effect.aa_change, None)

    def test_chr1_245019922_del_var(self):
        effects = VariantAnnotation.annotate_variant(self.gmDB, self.GA,
                                                     loc="1:245019922",
                                                     var="del(10)")
        self.assertEqual(len(effects), 2)
        effects_sorted = sorted(effects, key=lambda k: k.transcript_id)

        self.assertEqual(effects_sorted[0].gene, "HNRNPU")
        self.assertEqual(effects_sorted[0].transcript_id, "NM_004501_1")
        self.assertEqual(effects_sorted[0].strand, "-")
        self.assertEqual(effects_sorted[0].effect, "splice-site")
        self.assertEqual(effects_sorted[0].prot_pos, 563)
        self.assertEqual(effects_sorted[0].prot_length, 807)
        self.assertEqual(effects_sorted[0].aa_change, None)

        self.assertEqual(effects_sorted[1].gene, "HNRNPU")
        self.assertEqual(effects_sorted[1].transcript_id, "NM_031844_1")
        self.assertEqual(effects_sorted[1].strand, "-")
        self.assertEqual(effects_sorted[1].effect, "splice-site")
        self.assertEqual(effects_sorted[1].prot_pos, 582)
        self.assertEqual(effects_sorted[1].prot_length, 826)
        self.assertEqual(effects_sorted[1].aa_change, None)

    def test_chr9_140509156_ins_var(self):
        [effect] = VariantAnnotation.annotate_variant(self.gmDB, self.GA,
                                                      loc="9:140509156",
                                                      var="ins(AGGAGG)")

        self.assertEqual(effect.gene, "ARRDC1")
        self.assertEqual(effect.transcript_id, "NM_152285_1")
        self.assertEqual(effect.strand, "+")
        self.assertEqual(effect.effect, "no-frame-shift")
        self.assertEqual(effect.prot_pos, 314)
        self.assertEqual(effect.prot_length, 433)
        self.assertEqual(effect.aa_change, None)

    def test_chr12_130827138_del_var(self):
        effects = VariantAnnotation.annotate_variant(self.gmDB, self.GA,
                                                     loc="12:130827138",
                                                     var="del(4)")
        self.assertEqual(len(effects), 2)
        effects_sorted = sorted(effects, key=lambda k: k.transcript_id)

        self.assertEqual(effects_sorted[0].gene, "PIWIL1")
        self.assertEqual(effects_sorted[0].transcript_id, "NM_001190971_1")
        self.assertEqual(effects_sorted[0].strand, "+")
        self.assertEqual(effects_sorted[0].effect, "noStart")
        self.assertEqual(effects_sorted[0].prot_pos, 1)
        self.assertEqual(effects_sorted[0].prot_length, 830)
        self.assertEqual(effects_sorted[0].aa_change, None)

        self.assertEqual(effects_sorted[1].gene, "PIWIL1")
        self.assertEqual(effects_sorted[1].transcript_id, "NM_004764_1")
        self.assertEqual(effects_sorted[1].strand, "+")
        self.assertEqual(effects_sorted[1].effect, "noStart")
        self.assertEqual(effects_sorted[1].prot_pos, 1)
        self.assertEqual(effects_sorted[1].prot_length, 862)
        self.assertEqual(effects_sorted[1].aa_change, None)

    def test_chr20_57466823_sub_var(self):
        effects = VariantAnnotation.annotate_variant(self.gmDB, self.GA,
                                                     loc="20:57466823",
                                                     var="sub(C->T)")
        self.assertEqual(len(effects), 8)
        effects_sorted = sorted(effects, key=lambda k: k.transcript_id)

        self.assertEqual(effects_sorted[0].gene, "GNAS")
        self.assertEqual(effects_sorted[0].transcript_id, "NM_000516_1")
        self.assertEqual(effects_sorted[0].strand, "+")
        self.assertEqual(effects_sorted[0].effect, "synonymous")
        self.assertEqual(effects_sorted[0].prot_pos, 14)
        self.assertEqual(effects_sorted[0].prot_length, 394)
        self.assertEqual(effects_sorted[0].aa_change, "Asn->Asn")

        self.assertEqual(effects_sorted[1].gene, "GNAS")
        self.assertEqual(effects_sorted[1].transcript_id, "NM_001077488_1")
        self.assertEqual(effects_sorted[1].strand, "+")
        self.assertEqual(effects_sorted[1].effect, "synonymous")
        self.assertEqual(effects_sorted[1].prot_pos, 14)
        self.assertEqual(effects_sorted[1].prot_length, 395)
        self.assertEqual(effects_sorted[1].aa_change, "Asn->Asn")

        self.assertEqual(effects_sorted[2].gene, "GNAS")
        self.assertEqual(effects_sorted[2].transcript_id, "NM_001077489_1")
        self.assertEqual(effects_sorted[2].strand, "+")
        self.assertEqual(effects_sorted[2].effect, "synonymous")
        self.assertEqual(effects_sorted[2].prot_pos, 14)
        self.assertEqual(effects_sorted[2].prot_length, 379)
        self.assertEqual(effects_sorted[2].aa_change, "Asn->Asn")

        self.assertEqual(effects_sorted[3].gene, "GNAS")
        self.assertEqual(effects_sorted[3].transcript_id, "NM_001077490_1")
        self.assertEqual(effects_sorted[3].strand, "+")
        self.assertEqual(effects_sorted[3].effect, "3'UTR-intron")
        self.assertEqual(effects_sorted[3].prot_pos, None)
        self.assertEqual(effects_sorted[3].prot_length, None)
        self.assertEqual(effects_sorted[3].aa_change, None)

        self.assertEqual(effects_sorted[4].gene, "GNAS")
        self.assertEqual(effects_sorted[4].transcript_id, "NM_016592_1")
        self.assertEqual(effects_sorted[4].strand, "+")
        self.assertEqual(effects_sorted[4].effect, "3'UTR-intron")
        self.assertEqual(effects_sorted[4].prot_pos, None)
        self.assertEqual(effects_sorted[4].prot_length, None)
        self.assertEqual(effects_sorted[4].aa_change, None)

        self.assertEqual(effects_sorted[5].gene, "GNAS")
        self.assertEqual(effects_sorted[5].transcript_id, "NM_080425_1")
        self.assertEqual(effects_sorted[5].strand, "+")
        self.assertEqual(effects_sorted[5].effect, "intron")
        self.assertEqual(effects_sorted[5].prot_pos, 690)
        self.assertEqual(effects_sorted[5].prot_length, 1038)
        self.assertEqual(effects_sorted[5].aa_change, None)

        self.assertEqual(effects_sorted[6].gene, "GNAS")
        self.assertEqual(effects_sorted[6].transcript_id, "NM_080426_1")
        self.assertEqual(effects_sorted[6].strand, "+")
        self.assertEqual(effects_sorted[6].effect, "synonymous")
        self.assertEqual(effects_sorted[6].prot_pos, 14)
        self.assertEqual(effects_sorted[6].prot_length, 380)
        self.assertEqual(effects_sorted[6].aa_change, "Asn->Asn")

        self.assertEqual(effects_sorted[7].gene, "GNAS")
        self.assertEqual(effects_sorted[7].transcript_id, "NR_003259_1")
        self.assertEqual(effects_sorted[7].strand, "+")
        self.assertEqual(effects_sorted[7].effect, "non-coding-intron")
        self.assertEqual(effects_sorted[7].prot_pos, None)
        self.assertEqual(effects_sorted[7].prot_length, None)
        self.assertEqual(effects_sorted[7].aa_change, None)

    def test_chr1_156354348_del_var(self):
        effects = VariantAnnotation.annotate_variant(self.gmDB, self.GA,
                                                     loc="1:156354348",
                                                     var="del(1)")
        self.assertEqual(len(effects), 4)
        effects_sorted = sorted(effects, key=lambda k: k.transcript_id)

        self.assertEqual(effects_sorted[0].gene, "RHBG")
        self.assertEqual(effects_sorted[0].transcript_id, "NM_001256395_1")
        self.assertEqual(effects_sorted[0].strand, "+")
        self.assertEqual(effects_sorted[0].effect, "splice-site")
        self.assertEqual(effects_sorted[0].prot_pos, 353)
        self.assertEqual(effects_sorted[0].prot_length, 390)
        self.assertEqual(effects_sorted[0].aa_change, None)

        self.assertEqual(effects_sorted[1].gene, "RHBG")
        self.assertEqual(effects_sorted[1].transcript_id, "NM_001256396_1")
        self.assertEqual(effects_sorted[1].strand, "+")
        self.assertEqual(effects_sorted[1].effect, "splice-site")
        self.assertEqual(effects_sorted[1].prot_pos, 392)
        self.assertEqual(effects_sorted[1].prot_length, 429)
        self.assertEqual(effects_sorted[1].aa_change, None)

        self.assertEqual(effects_sorted[2].gene, "RHBG")
        self.assertEqual(effects_sorted[2].transcript_id, "NM_020407_1")
        self.assertEqual(effects_sorted[2].strand, "+")
        self.assertEqual(effects_sorted[2].effect, "splice-site")
        self.assertEqual(effects_sorted[2].prot_pos, 422)
        self.assertEqual(effects_sorted[2].prot_length, 459)
        self.assertEqual(effects_sorted[2].aa_change, None)

        self.assertEqual(effects_sorted[3].gene, "RHBG")
        self.assertEqual(effects_sorted[3].transcript_id, "NR_046115_1")
        self.assertEqual(effects_sorted[3].strand, "+")
        self.assertEqual(effects_sorted[3].effect, "non-coding")
        self.assertEqual(effects_sorted[3].prot_pos, None)
        self.assertEqual(effects_sorted[3].prot_length, None)
        self.assertEqual(effects_sorted[3].aa_change, None)


if __name__ == "__main__":
    unittest.main()
