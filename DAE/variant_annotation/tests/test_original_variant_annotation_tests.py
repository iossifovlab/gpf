from __future__ import unicode_literals
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
                                                      chrom="1",
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
        # self.assertEqual(effect.aa_change, None)

    def test_intron_var(self):
        [effect] = VariantAnnotation.annotate_variant(self.gmDB, self.GA,
                                                      loc="1:53287094",
                                                      var="ins(G)")
        self.assertEqual(effect.gene, "ZYG11B")
        self.assertEqual(effect.transcript_id, "NM_024646_1")
        self.assertEqual(effect.strand, "+")
        self.assertEqual(effect.effect, "intron")
        self.assertEqual(effect.prot_pos, 682)
        self.assertEqual(effect.prot_length, 744)
        self.assertEqual(effect.aa_change, None)
        self.assertEqual(effect.which_intron, 13)
        self.assertEqual(effect.how_many_introns, 13)
        self.assertEqual(effect.dist_from_coding, 17)
        self.assertEqual(effect.dist_from_acceptor, 17)
        self.assertEqual(effect.dist_from_donor, 4792)
        self.assertEqual(effect.intron_length, 4809)

    def test_no_start_var(self):
        effects = VariantAnnotation.annotate_variant(self.gmDB, self.GA,
                                                     loc="17:74729179",
                                                     var="del(3)")

        self.assertEqual(len(effects), 7)
        for effect in effects:
            self.assertEqual(effect.gene, "METTL23")
            self.assertEqual(effect.strand, "+")

        print(effects)

        effect = effects.pop(0)
        self.assertEqual(effect.transcript_id, "NM_001080510_1")
        self.assertEqual(effect.effect, "no-frame-shift")
        self.assertEqual(effect.prot_pos, 68)
        self.assertEqual(effect.prot_length, 190)
        self.assertEqual(effect.aa_change, "Met,Asn->Ile")

        effect = effects.pop(0)
        self.assertEqual(effect.transcript_id, "NM_001206983_1")
        self.assertEqual(effect.effect, "no-frame-shift")
        self.assertEqual(effect.prot_pos, 68)
        self.assertEqual(effect.prot_length, 190)
        self.assertEqual(effect.aa_change, "Met,Asn->Ile")

        effect = effects.pop(0)
        self.assertEqual(effect.transcript_id, "NM_001206984_1")
        self.assertEqual(effect.effect, "no-frame-shift")
        self.assertEqual(effect.prot_pos, 68)
        self.assertEqual(effect.prot_length, 190)
        self.assertEqual(effect.aa_change, "Met,Asn->Ile")

        effect = effects.pop(0)
        self.assertEqual(effect.transcript_id, "NM_001206985_1")
        self.assertEqual(effect.effect, "noStart")
        self.assertEqual(effect.prot_pos, 1)
        self.assertEqual(effect.prot_length, 123)
        self.assertEqual(effect.aa_change, None)

        effect = effects.pop(0)
        self.assertEqual(effect.transcript_id, "NM_001206986_1")
        self.assertEqual(effect.effect, "noStart")
        self.assertEqual(effect.prot_pos, 1)
        self.assertEqual(effect.prot_length, 123)
        self.assertEqual(effect.aa_change, None)

        effect = effects.pop(0)
        self.assertEqual(effect.transcript_id, "NM_001206987_1")
        self.assertEqual(effect.effect, "noStart")
        self.assertEqual(effect.prot_pos, 1)
        self.assertEqual(effect.prot_length, 123)
        self.assertEqual(effect.aa_change, None)

        effect = effects.pop(0)
        self.assertEqual(effect.transcript_id, "NR_038193_1")
        self.assertEqual(effect.effect, "non-coding-intron")
        self.assertEqual(effect.prot_pos, None)
        self.assertEqual(effect.prot_length, None)
        self.assertEqual(effect.aa_change, None)

    def test_frame_shift_var(self):
        effects = VariantAnnotation.annotate_variant(self.gmDB, self.GA,
                                                     loc="2:238617257",
                                                     var="ins(A)")
        self.assertEqual(len(effects), 5)
        print(effects)

        effect = effects.pop(0)
        self.assertEqual(effect.gene, "LRRFIP1")
        self.assertEqual(effect.transcript_id, "NM_001137550_1")
        self.assertEqual(effect.strand, "+")
        self.assertEqual(effect.effect, "frame-shift")
        self.assertEqual(effect.prot_pos, 56)
        self.assertEqual(effect.prot_length, 640)
        # self.assertEqual(effect.aa_change, None)

        effect = effects.pop(0)
        self.assertEqual(effect.gene, "LRRFIP1")
        self.assertEqual(effect.transcript_id, "NM_001137551_1")
        self.assertEqual(effect.strand, "+")
        self.assertEqual(effect.effect, "frame-shift")
        self.assertEqual(effect.prot_pos, 46)
        self.assertEqual(effect.prot_length, 394)
        # self.assertEqual(effect.aa_change, None)

        effect = effects.pop(0)
        self.assertEqual(effect.gene, "LRRFIP1")
        self.assertEqual(effect.transcript_id, "NM_001137552_1")
        self.assertEqual(effect.strand, "+")
        self.assertEqual(effect.effect, "frame-shift")
        self.assertEqual(effect.prot_pos, 46)
        self.assertEqual(effect.prot_length, 808)
        # self.assertEqual(effect.aa_change, None)

        effect = effects.pop(0)
        self.assertEqual(effect.gene, "LRRFIP1")
        self.assertEqual(effect.transcript_id, "NM_001137553_1")
        self.assertEqual(effect.strand, "+")
        self.assertEqual(effect.effect, "frame-shift")
        self.assertEqual(effect.prot_pos, 46)
        self.assertEqual(effect.prot_length, 752)
        # self.assertEqual(effect.aa_change, None)

        effect = effects.pop(0)
        self.assertEqual(effect.gene, "LRRFIP1")
        self.assertEqual(effect.transcript_id, "NM_004735_1")
        self.assertEqual(effect.strand, "+")
        self.assertEqual(effect.effect, "frame-shift")
        self.assertEqual(effect.prot_pos, 46)
        self.assertEqual(effect.prot_length, 784)
        # self.assertEqual(effect.aa_change, None)

    def test_no_frame_shift_var(self):
        effects = VariantAnnotation.annotate_variant(self.gmDB, self.GA,
                                                     loc="1:24507340",
                                                     var="del(3)")
        self.assertEqual(len(effects), 3)

        print(effects)

        effect = effects.pop(0)
        self.assertEqual(effect.gene, "IFNLR1")
        self.assertEqual(effect.transcript_id, "NM_170743_1")
        self.assertEqual(effect.strand, "-")
        self.assertEqual(effect.effect, "no-frame-shift")
        self.assertEqual(effect.prot_pos, 21)
        self.assertEqual(effect.prot_length, 520)
        self.assertEqual(effect.aa_change, "Arg->")

        effect = effects.pop(0)
        self.assertEqual(effect.gene, "IFNLR1")
        self.assertEqual(effect.transcript_id, "NM_173064_1")
        self.assertEqual(effect.strand, "-")
        self.assertEqual(effect.effect, "no-frame-shift")
        self.assertEqual(effect.prot_pos, 21)
        self.assertEqual(effect.prot_length, 491)
        self.assertEqual(effect.aa_change, "Arg->")

        effect = effects.pop(0)
        self.assertEqual(effect.gene, "IFNLR1")
        self.assertEqual(effect.transcript_id, "NM_173065_1")
        self.assertEqual(effect.strand, "-")
        self.assertEqual(effect.effect, "no-frame-shift")
        self.assertEqual(effect.prot_pos, 21)
        self.assertEqual(effect.prot_length, 244)
        self.assertEqual(effect.aa_change, "Arg->")

    def test_nonsense_var(self):
        effects = VariantAnnotation.annotate_variant(self.gmDB, self.GA,
                                                     loc="1:61553905",
                                                     var="sub(C->T)")
        self.assertEqual(len(effects), 4)
        print(effects)

        effect = effects[0]
        self.assertEqual(effect.gene, "NFIA")
        self.assertEqual(effect.transcript_id, "NM_001134673_1")
        self.assertEqual(effect.strand, "+")
        self.assertEqual(effect.effect, "nonsense")
        self.assertEqual(effect.prot_pos, 38)
        self.assertEqual(effect.prot_length, 509)
        self.assertEqual(effect.aa_change, "Arg->End")

        effect = effects[1]
        self.assertEqual(effect.gene, "NFIA")
        self.assertEqual(effect.transcript_id, "NM_005595_1")
        self.assertEqual(effect.strand, "+")
        self.assertEqual(effect.effect, "nonsense")
        self.assertEqual(effect.prot_pos, 38)
        self.assertEqual(effect.prot_length, 498)
        self.assertEqual(effect.aa_change, "Arg->End")

        effect = effects[2]
        self.assertEqual(effect.gene, "NFIA")
        self.assertEqual(effect.transcript_id, "NM_001145511_1")
        self.assertEqual(effect.strand, "+")
        self.assertEqual(effect.effect, "nonsense")
        self.assertEqual(effect.prot_pos, 30)
        self.assertEqual(effect.prot_length, 501)
        self.assertEqual(effect.aa_change, "Arg->End")

        effect = effects[3]
        self.assertEqual(effect.gene, "NFIA")
        self.assertEqual(effect.transcript_id, "NM_001145512_1")
        self.assertEqual(effect.strand, "+")
        self.assertEqual(effect.effect, "nonsense")
        self.assertEqual(effect.prot_pos, 83)
        self.assertEqual(effect.prot_length, 554)
        self.assertEqual(effect.aa_change, "Arg->End")

    def test_splice_site_var(self):
        effects = VariantAnnotation.annotate_variant(self.gmDB, self.GA,
                                                     loc="1:67878948",
                                                     var="sub(T->G)")
        self.assertEqual(len(effects), 4)

        effect = effects[0]
        self.assertEqual(effect.gene, "SERBP1")
        self.assertEqual(effect.transcript_id, "NM_001018067_1")
        self.assertEqual(effect.strand, "-")
        self.assertEqual(effect.effect, "splice-site")
        self.assertEqual(effect.prot_pos, 391)
        self.assertEqual(effect.prot_length, 408)
        self.assertEqual(effect.aa_change, None)
        self.assertEqual(effect.which_intron, 7)
        self.assertEqual(effect.how_many_introns, 7)
        self.assertEqual(effect.dist_from_coding, 1)
        self.assertEqual(effect.dist_from_acceptor, 1)
        self.assertEqual(effect.dist_from_donor, 1900)
        self.assertEqual(effect.intron_length, 1902)

        effect = effects[1]
        self.assertEqual(effect.gene, "SERBP1")
        self.assertEqual(effect.transcript_id, "NM_001018068_1")
        self.assertEqual(effect.strand, "-")
        self.assertEqual(effect.effect, "splice-site")
        self.assertEqual(effect.prot_pos, 385)
        self.assertEqual(effect.prot_length, 402)
        self.assertEqual(effect.aa_change, None)
        self.assertEqual(effect.which_intron, 7)
        self.assertEqual(effect.how_many_introns, 7)
        self.assertEqual(effect.dist_from_coding, 1)
        self.assertEqual(effect.dist_from_acceptor, 1)
        self.assertEqual(effect.dist_from_donor, 1900)
        self.assertEqual(effect.intron_length, 1902)

        effect = effects[2]
        self.assertEqual(effect.gene, "SERBP1")
        self.assertEqual(effect.transcript_id, "NM_001018069_1")
        self.assertEqual(effect.strand, "-")
        self.assertEqual(effect.effect, "splice-site")
        self.assertEqual(effect.prot_pos, 376)
        self.assertEqual(effect.prot_length, 393)
        self.assertEqual(effect.aa_change, None)
        self.assertEqual(effect.which_intron, 7)
        self.assertEqual(effect.how_many_introns, 7)
        self.assertEqual(effect.dist_from_coding, 1)
        self.assertEqual(effect.dist_from_acceptor, 1)
        self.assertEqual(effect.dist_from_donor, 1900)
        self.assertEqual(effect.intron_length, 1902)

        effect = effects[3]
        self.assertEqual(effect.gene, "SERBP1")
        self.assertEqual(effect.transcript_id, "NM_015640_1")
        self.assertEqual(effect.strand, "-")
        self.assertEqual(effect.effect, "splice-site")
        self.assertEqual(effect.prot_pos, 370)
        self.assertEqual(effect.prot_length, 387)
        self.assertEqual(effect.aa_change, None)
        self.assertEqual(effect.which_intron, 7)
        self.assertEqual(effect.how_many_introns, 7)
        self.assertEqual(effect.dist_from_coding, 1)
        self.assertEqual(effect.dist_from_acceptor, 1)
        self.assertEqual(effect.dist_from_donor, 1900)
        self.assertEqual(effect.intron_length, 1902)

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
        self.assertEqual(effect.aa_change, "Gln->Gln,End")

    def test_no_end_var(self):
        [effect] = VariantAnnotation.annotate_variant(self.gmDB, self.GA,
                                                      loc="19:8645778",
                                                      var="del(9)")
        self.assertEqual(effect.gene, "ADAMTS10")
        self.assertEqual(effect.transcript_id, "NM_030957_1")
        self.assertEqual(effect.strand, "-")
        self.assertEqual(effect.effect, "noEnd")
        self.assertEqual(effect.prot_pos, 1101)
        self.assertEqual(effect.prot_length, 1103)
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
        self.assertEqual(effects[0].prot_length, 101)
        self.assertEqual(effects[0].aa_change, None)
        self.assertEqual(effects[0].dist_from_coding, 258)

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
        self.assertEqual(effect.prot_length, 728)
        self.assertEqual(effect.aa_change, None)
        self.assertEqual(effect.dist_from_coding, 2)

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
        self.assertEqual(effect.prot_pos, 483)
        self.assertEqual(effect.prot_length, 540)
        self.assertEqual(effect.aa_change, None)
        self.assertEqual(effect.which_intron, 12)
        self.assertEqual(effect.how_many_introns, 12)
        self.assertEqual(effect.dist_from_coding, 1)
        self.assertEqual(effect.dist_from_acceptor, 6915)
        self.assertEqual(effect.dist_from_donor, 1)
        self.assertEqual(effect.intron_length, 6917)

    def test_splice_site_del_neg_strand_var(self):
        [effect] = VariantAnnotation.annotate_variant(self.gmDB, self.GA,
                                                      loc="4:48523230",
                                                      var="del(4)")
        self.assertEqual(effect.gene, "FRYL")
        self.assertEqual(effect.transcript_id, "NM_015030_1")
        self.assertEqual(effect.strand, "-")
        self.assertEqual(effect.effect, "splice-site")
        self.assertEqual(effect.prot_pos, 2508)
        self.assertEqual(effect.prot_length, 3013)
        self.assertEqual(effect.aa_change, None)
        self.assertEqual(effect.which_intron, 54)
        self.assertEqual(effect.how_many_introns, 63)
        self.assertEqual(effect.dist_from_coding, -3)
        self.assertEqual(effect.dist_from_acceptor, -3)
        self.assertEqual(effect.dist_from_donor, 1684)
        self.assertEqual(effect.intron_length, 1685)

    def test_splice_site_ins_pos_strand_var(self):
        [effect] = VariantAnnotation.annotate_variant(self.gmDB, self.GA,
                                                      loc="7:24720141",
                                                      var="ins(C)")
        self.assertEqual(effect.gene, "MPP6")
        self.assertEqual(effect.transcript_id, "NM_016447_1")
        self.assertEqual(effect.strand, "+")
        self.assertEqual(effect.effect, "splice-site")
        self.assertEqual(effect.prot_pos, 483)
        self.assertEqual(effect.prot_length, 540)
        self.assertEqual(effect.aa_change, None)
        self.assertEqual(effect.which_intron, 12)
        self.assertEqual(effect.how_many_introns, 12)
        self.assertEqual(effect.dist_from_coding, 1)
        self.assertEqual(effect.dist_from_acceptor, 6916)
        self.assertEqual(effect.dist_from_donor, 1)
        self.assertEqual(effect.intron_length, 6917)

    def test_splice_site_ins_neg_strand_var(self):
        [effect] = VariantAnnotation.annotate_variant(self.gmDB, self.GA,
                                                      loc="12:116418554",
                                                      var="ins(C)")
        self.assertEqual(effect.gene, "MED13L")
        self.assertEqual(effect.transcript_id, "NM_015335_1")
        self.assertEqual(effect.strand, "-")
        self.assertEqual(effect.effect, "splice-site")
        self.assertEqual(effect.prot_pos, 1789)
        self.assertEqual(effect.prot_length, 2210)
        self.assertEqual(effect.aa_change, None)
        self.assertEqual(effect.which_intron, 23)
        self.assertEqual(effect.how_many_introns, 30)
        self.assertEqual(effect.dist_from_coding, 1)
        self.assertEqual(effect.dist_from_acceptor, 5010)
        self.assertEqual(effect.dist_from_donor, 1)
        self.assertEqual(effect.intron_length, 5011)

    def test_first_codon_ins_noEnd_var(self):
        [effect] = VariantAnnotation.annotate_variant(self.gmDB, self.GA,
                                                      loc="1:3407093",
                                                      var="ins(A)")
        self.assertEqual(effect.gene, "MEGF6")
        self.assertEqual(effect.transcript_id, "NM_001409_1")
        self.assertEqual(effect.strand, "-")
        self.assertEqual(effect.effect, "noEnd")
        self.assertEqual(effect.prot_pos, 1542)
        self.assertEqual(effect.prot_length, 1541)
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
        self.assertEqual(effect.prot_length, 540)
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
        self.assertEqual(effect.prot_length, 540)
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
        self.assertEqual(effects_sorted[0].prot_length, 390)
        self.assertEqual(effects_sorted[0].aa_change, None)
        self.assertEqual(effects_sorted[0].dist_from_coding, 136)

        self.assertEqual(effects_sorted[1].gene, "PTGER3")
        self.assertEqual(effects_sorted[1].transcript_id, "NM_198714_1")
        self.assertEqual(effects_sorted[1].strand, "-")
        self.assertEqual(effects_sorted[1].effect, "3'UTR-intron")
        self.assertEqual(effects_sorted[1].prot_pos, None)
        self.assertEqual(effects_sorted[1].prot_length, 390)
        self.assertEqual(effects_sorted[1].aa_change, None)

        self.assertEqual(effects_sorted[2].gene, "PTGER3")
        self.assertEqual(effects_sorted[2].transcript_id, "NM_198716_1")
        self.assertEqual(effects_sorted[2].strand, "-")
        self.assertEqual(effects_sorted[2].effect, "intron")
        self.assertEqual(effects_sorted[2].prot_pos, 369)
        self.assertEqual(effects_sorted[2].prot_length, 374)
        self.assertEqual(effects_sorted[2].aa_change, None)
        self.assertEqual(effects_sorted[2].which_intron, 3)
        self.assertEqual(effects_sorted[2].how_many_introns, 3)
        self.assertEqual(effects_sorted[2].dist_from_coding, 815)
        self.assertEqual(effects_sorted[2].dist_from_acceptor, 100087)
        self.assertEqual(effects_sorted[2].dist_from_donor, 815)
        self.assertEqual(effects_sorted[2].intron_length, 100903)

        self.assertEqual(effects_sorted[3].gene, "PTGER3")
        self.assertEqual(effects_sorted[3].transcript_id, "NM_198717_1")
        self.assertEqual(effects_sorted[3].strand, "-")
        self.assertEqual(effects_sorted[3].effect, "intron")
        self.assertEqual(effects_sorted[3].prot_pos, 360)
        self.assertEqual(effects_sorted[3].prot_length, 365)
        self.assertEqual(effects_sorted[3].aa_change, None)
        self.assertEqual(effects_sorted[3].which_intron, 2)
        self.assertEqual(effects_sorted[3].how_many_introns, 2)
        self.assertEqual(effects_sorted[3].dist_from_coding, 59357)
        self.assertEqual(effects_sorted[3].dist_from_acceptor, 100087)
        self.assertEqual(effects_sorted[3].dist_from_donor, 59357)
        self.assertEqual(effects_sorted[3].intron_length, 159445)

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
        self.assertEqual(effects_sorted[0].aa_change, "Gly->Ala,Ala,Gly")

        self.assertEqual(effects_sorted[1].gene, "PMEPA1")
        self.assertEqual(effects_sorted[1].transcript_id, "NM_199169_1")
        self.assertEqual(effects_sorted[1].strand, "-")
        self.assertEqual(effects_sorted[1].effect, "intron")
        self.assertEqual(effects_sorted[1].prot_pos, 2)
        self.assertEqual(effects_sorted[1].prot_length, 252)
        self.assertEqual(effects_sorted[1].aa_change, None)
        self.assertEqual(effects_sorted[1].which_intron, 1)
        self.assertEqual(effects_sorted[1].how_many_introns, 3)
        self.assertEqual(effects_sorted[1].dist_from_coding, 923)
        self.assertEqual(effects_sorted[1].dist_from_acceptor, 49839)
        self.assertEqual(effects_sorted[1].dist_from_donor, 923)
        self.assertEqual(effects_sorted[1].intron_length, 50762)

        self.assertEqual(effects_sorted[2].gene, "PMEPA1")
        self.assertEqual(effects_sorted[2].transcript_id, "NM_199170_1")
        self.assertEqual(effects_sorted[2].strand, "-")
        self.assertEqual(effects_sorted[2].effect, "5'UTR-intron")
        self.assertEqual(effects_sorted[2].prot_pos, None)
        self.assertEqual(effects_sorted[2].prot_length, 237)
        self.assertEqual(effects_sorted[2].aa_change, None)

        self.assertEqual(effects_sorted[3].gene, "PMEPA1")
        self.assertEqual(effects_sorted[3].transcript_id, "NM_199171_1")
        self.assertEqual(effects_sorted[3].strand, "-")
        self.assertEqual(effects_sorted[3].effect, "5'UTR-intron")
        self.assertEqual(effects_sorted[3].prot_pos, None)
        self.assertEqual(effects_sorted[3].prot_length, 237)
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
        self.assertEqual(effects_sorted[3].prot_length, 626)
        self.assertEqual(effects_sorted[3].aa_change, None)
        self.assertEqual(effects_sorted[3].dist_from_coding, 186)

        self.assertEqual(effects_sorted[4].gene, "GNAS")
        self.assertEqual(effects_sorted[4].transcript_id, "NM_016592_1")
        self.assertEqual(effects_sorted[4].strand, "+")
        self.assertEqual(effects_sorted[4].effect, "3'UTR")
        self.assertEqual(effects_sorted[4].prot_pos, None)
        self.assertEqual(effects_sorted[4].prot_length, 245)
        self.assertEqual(effects_sorted[4].aa_change, None)
        self.assertEqual(effects_sorted[4].dist_from_coding, 231)

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
        self.assertEqual(effects_sorted[0].prot_length, 92)
        self.assertEqual(effects_sorted[0].aa_change, None)

        self.assertEqual(effects_sorted[1].gene, "SNW1")
        self.assertEqual(effects_sorted[1].transcript_id, "NM_012245_1")
        self.assertEqual(effects_sorted[1].strand, "-")
        self.assertEqual(effects_sorted[1].effect, "5'UTR")
        self.assertEqual(effects_sorted[1].prot_pos, None)
        self.assertEqual(effects_sorted[1].prot_length, 536)
        self.assertEqual(effects_sorted[1].aa_change, None)
        self.assertEqual(effects_sorted[1].dist_from_coding, 1)

        self.assertEqual(effects_sorted[2].gene, "C14orf178")
        self.assertEqual(effects_sorted[2].transcript_id, "NM_174943_1")
        self.assertEqual(effects_sorted[2].strand, "+")
        self.assertEqual(effects_sorted[2].effect, "intron")
        self.assertEqual(effects_sorted[2].prot_pos, 25)
        self.assertEqual(effects_sorted[2].prot_length, 122)
        self.assertEqual(effects_sorted[2].aa_change, None)
        self.assertEqual(effects_sorted[2].which_intron, 1)
        self.assertEqual(effects_sorted[2].how_many_introns, 2)
        self.assertEqual(effects_sorted[2].dist_from_coding, 11)
        self.assertEqual(effects_sorted[2].dist_from_acceptor, 7315)
        self.assertEqual(effects_sorted[2].dist_from_donor, 11)
        self.assertEqual(effects_sorted[2].intron_length, 7335)

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
        self.assertEqual(effects_sorted[0].prot_length, 2581)
        self.assertEqual(effects_sorted[0].aa_change, None)
        self.assertEqual(effects_sorted[0].which_intron, 3)
        self.assertEqual(effects_sorted[0].how_many_introns, 36)
        self.assertEqual(effects_sorted[0].dist_from_coding, -9)
        self.assertEqual(effects_sorted[0].dist_from_acceptor, 1588)
        self.assertEqual(effects_sorted[0].dist_from_donor, -9)
        self.assertEqual(effects_sorted[0].intron_length, 1626)

        self.assertEqual(effects_sorted[1].gene, "CHD8")
        self.assertEqual(effects_sorted[1].transcript_id, "NM_020920_1")
        self.assertEqual(effects_sorted[1].strand, "-")
        self.assertEqual(effects_sorted[1].effect, "splice-site")
        self.assertEqual(effects_sorted[1].prot_pos, 255)
        self.assertEqual(effects_sorted[1].prot_length, 2302)
        self.assertEqual(effects_sorted[1].aa_change, None)
        self.assertEqual(effects_sorted[1].which_intron, 4)
        self.assertEqual(effects_sorted[1].how_many_introns, 37)
        self.assertEqual(effects_sorted[1].dist_from_coding, -9)
        self.assertEqual(effects_sorted[1].dist_from_acceptor, 1588)
        self.assertEqual(effects_sorted[1].dist_from_donor, -9)
        self.assertEqual(effects_sorted[1].intron_length, 1626)

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
        self.assertEqual(effects_sorted[0].prot_length, 595)
        self.assertEqual(effects_sorted[0].aa_change, None)
        self.assertEqual(effects_sorted[0].which_intron, 8)
        self.assertEqual(effects_sorted[0].how_many_introns, 14)
        self.assertEqual(effects_sorted[0].dist_from_coding, 0)
        self.assertEqual(effects_sorted[0].dist_from_acceptor, 7553)
        self.assertEqual(effects_sorted[0].dist_from_donor, 0)
        self.assertEqual(effects_sorted[0].intron_length, 7554)

        self.assertEqual(effects_sorted[1].gene, "TNFRSF8")
        self.assertEqual(effects_sorted[1].transcript_id, "NM_001281430_1")
        self.assertEqual(effects_sorted[1].strand, "+")
        self.assertEqual(effects_sorted[1].effect, "splice-site")
        self.assertEqual(effects_sorted[1].prot_pos, 205)
        self.assertEqual(effects_sorted[1].prot_length, 483)
        self.assertEqual(effects_sorted[1].aa_change, None)
        self.assertEqual(effects_sorted[1].which_intron, 7)
        self.assertEqual(effects_sorted[1].how_many_introns, 13)
        self.assertEqual(effects_sorted[1].dist_from_coding, 0)
        self.assertEqual(effects_sorted[1].dist_from_acceptor, 7553)
        self.assertEqual(effects_sorted[1].dist_from_donor, 0)
        self.assertEqual(effects_sorted[1].intron_length, 7554)

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
        self.assertEqual(effects_sorted[0].prot_length, 4432)
        self.assertEqual(effects_sorted[0].aa_change, "End->End")

        self.assertEqual(effects_sorted[1].gene, "SACS")
        self.assertEqual(effects_sorted[1].transcript_id, "NM_014363_1")
        self.assertEqual(effects_sorted[1].strand, "-")
        self.assertEqual(effects_sorted[1].effect, "synonymous")
        self.assertEqual(effects_sorted[1].prot_pos, 4580)
        self.assertEqual(effects_sorted[1].prot_length, 4579)
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
        self.assertEqual(effects_sorted[0].prot_length, 500)
        self.assertEqual(effects_sorted[0].aa_change, None)
        self.assertEqual(effects_sorted[0].which_intron, 5)
        self.assertEqual(effects_sorted[0].how_many_introns, 5)
        self.assertEqual(effects_sorted[0].dist_from_coding, 3540)
        self.assertEqual(effects_sorted[0].dist_from_acceptor, 3540)
        self.assertEqual(effects_sorted[0].dist_from_donor, 8375)
        self.assertEqual(effects_sorted[0].intron_length, 11918)

        self.assertEqual(effects_sorted[1].gene, "DPH3P1")
        self.assertEqual(effects_sorted[1].transcript_id, "NM_080750_1")
        self.assertEqual(effects_sorted[1].strand, "+")
        self.assertEqual(effects_sorted[1].effect, "5'UTR")
        self.assertEqual(effects_sorted[1].prot_pos, None)
        self.assertEqual(effects_sorted[1].prot_length, 78)
        self.assertEqual(effects_sorted[1].aa_change, None)
        self.assertEqual(effects_sorted[1].dist_from_coding, 24)

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
        self.assertEqual(effect.aa_change, "Arg->Arg,Glu,Leu")

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
        self.assertEqual(effects_sorted[2].prot_length, 302)
        self.assertEqual(effects_sorted[2].aa_change, None)
        self.assertEqual(effects_sorted[2].dist_from_coding, 129)

        self.assertEqual(effects_sorted[3].gene, "GPBP1")
        self.assertEqual(effects_sorted[3].transcript_id, "NM_022913_1")
        self.assertEqual(effects_sorted[3].strand, "+")
        self.assertEqual(effects_sorted[3].effect, "missense")
        self.assertEqual(effects_sorted[3].prot_pos, 129)
        self.assertEqual(effects_sorted[3].prot_length, 473)
        self.assertEqual(effects_sorted[3].aa_change, "Arg->Cys")

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
        self.assertEqual(effects_sorted[0].aa_change, "Glu,Arg->Glu")

        self.assertEqual(effects_sorted[1].gene, "RNF4")
        self.assertEqual(effects_sorted[1].transcript_id, "NM_001185010_1")
        self.assertEqual(effects_sorted[1].strand, "+")
        self.assertEqual(effects_sorted[1].effect, "intron")
        self.assertEqual(effects_sorted[1].prot_pos, 72)
        self.assertEqual(effects_sorted[1].prot_length, 113)
        self.assertEqual(effects_sorted[1].aa_change, None)
        self.assertEqual(effects_sorted[1].which_intron, 5)
        self.assertEqual(effects_sorted[1].how_many_introns, 6)
        self.assertEqual(effects_sorted[1].dist_from_coding, 473)
        self.assertEqual(effects_sorted[1].dist_from_acceptor, 641)
        self.assertEqual(effects_sorted[1].dist_from_donor, 473)
        self.assertEqual(effects_sorted[1].intron_length, 1117)

        self.assertEqual(effects_sorted[2].gene, "RNF4")
        self.assertEqual(effects_sorted[2].transcript_id, "NM_002938_1")
        self.assertEqual(effects_sorted[2].strand, "+")
        self.assertEqual(effects_sorted[2].effect, "no-frame-shift")
        self.assertEqual(effects_sorted[2].prot_pos, 72)
        self.assertEqual(effects_sorted[2].prot_length, 190)
        self.assertEqual(effects_sorted[2].aa_change, "Glu,Arg->Glu")

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
        self.assertEqual(effects_sorted[0].prot_length, 146)
        self.assertEqual(effects_sorted[0].aa_change, None)

        self.assertEqual(effects_sorted[1].gene, "ST20-MTHFS")
        self.assertEqual(effects_sorted[1].transcript_id, "NM_001199760_1")
        self.assertEqual(effects_sorted[1].strand, "-")
        self.assertEqual(effects_sorted[1].effect, "noEnd")
        self.assertEqual(effects_sorted[1].prot_pos, 180)
        self.assertEqual(effects_sorted[1].prot_length, 179)
        self.assertEqual(effects_sorted[1].aa_change, None)

        self.assertEqual(effects_sorted[2].gene, "MTHFS")
        self.assertEqual(effects_sorted[2].transcript_id, "NM_006441_1")
        self.assertEqual(effects_sorted[2].strand, "-")
        self.assertEqual(effects_sorted[2].effect, "noEnd")
        self.assertEqual(effects_sorted[2].prot_pos, 204)
        self.assertEqual(effects_sorted[2].prot_length, 203)
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
        self.assertEqual(effect.aa_change, "Asp,Leu,Glu->Glu")

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
        self.assertEqual(effects_sorted[0].prot_length, 147)
        self.assertEqual(effects_sorted[0].aa_change, None)

        self.assertEqual(effects_sorted[1].gene, "MGST2")
        self.assertEqual(effects_sorted[1].transcript_id, "NM_001204367_1")
        self.assertEqual(effects_sorted[1].strand, "+")
        self.assertEqual(effects_sorted[1].effect, "3'UTR-intron")
        self.assertEqual(effects_sorted[1].prot_pos, None)
        self.assertEqual(effects_sorted[1].prot_length, 79)
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
        self.assertEqual(effects_sorted[0].aa_change, "->Gly,Arg")

        self.assertEqual(effects_sorted[1].gene, "CDK13")
        self.assertEqual(effects_sorted[1].transcript_id, "NM_031267_1")
        self.assertEqual(effects_sorted[1].strand, "+")
        self.assertEqual(effects_sorted[1].effect, "no-frame-shift")
        self.assertEqual(effects_sorted[1].prot_pos, 1443)
        self.assertEqual(effects_sorted[1].prot_length, 1452)
        self.assertEqual(effects_sorted[1].aa_change, "->Gly,Arg")

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
        self.assertEqual(effects_sorted[0].prot_length, 1381)
        self.assertEqual(effects_sorted[0].aa_change, None)
        self.assertEqual(effects_sorted[0].dist_from_coding, 349)

        self.assertEqual(effects_sorted[1].gene, "PTCH1")
        self.assertEqual(effects_sorted[1].transcript_id, "NM_001083603_1")
        self.assertEqual(effects_sorted[1].strand, "-")
        self.assertEqual(effects_sorted[1].effect, "noStart")
        self.assertEqual(effects_sorted[1].prot_pos, 1)
        self.assertEqual(effects_sorted[1].prot_length, 1446)
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
        self.assertEqual(effects_sorted[0].aa_change, "Asp->")

        self.assertEqual(effects_sorted[1].gene, "CSRNP3")
        self.assertEqual(effects_sorted[1].transcript_id, "NM_024969_1")
        self.assertEqual(effects_sorted[1].strand, "+")
        self.assertEqual(effects_sorted[1].effect, "no-frame-shift")
        self.assertEqual(effects_sorted[1].prot_pos, 386)
        self.assertEqual(effects_sorted[1].prot_length, 585)
        self.assertEqual(effects_sorted[1].aa_change, "Asp->")

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
        self.assertEqual(effect.aa_change, "His,Asp->His")

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
        self.assertEqual(effects_sorted[2].prot_length, 536)
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
        self.assertEqual(effects_sorted[5].prot_length, 537)
        self.assertEqual(effects_sorted[5].aa_change, None)

        self.assertEqual(effects_sorted[6].gene, "CPNE1")
        self.assertEqual(effects_sorted[6].transcript_id, "NM_152926_1")
        self.assertEqual(effects_sorted[6].strand, "-")
        self.assertEqual(effects_sorted[6].effect, "5'UTR-intron")
        self.assertEqual(effects_sorted[6].prot_pos, None)
        self.assertEqual(effects_sorted[6].prot_length, 537)
        self.assertEqual(effects_sorted[6].aa_change, None)

        self.assertEqual(effects_sorted[7].gene, "CPNE1")
        self.assertEqual(effects_sorted[7].transcript_id, "NM_152927_1")
        self.assertEqual(effects_sorted[7].strand, "-")
        self.assertEqual(effects_sorted[7].effect, "5'UTR-intron")
        self.assertEqual(effects_sorted[7].prot_pos, None)
        self.assertEqual(effects_sorted[7].prot_length, 537)
        self.assertEqual(effects_sorted[7].aa_change, None)

        self.assertEqual(effects_sorted[8].gene, "CPNE1")
        self.assertEqual(effects_sorted[8].transcript_id, "NM_152928_1")
        self.assertEqual(effects_sorted[8].strand, "-")
        self.assertEqual(effects_sorted[8].effect, "5'UTR-intron")
        self.assertEqual(effects_sorted[8].prot_pos, None)
        self.assertEqual(effects_sorted[8].prot_length, 537)
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
        self.assertEqual(effects_sorted[0].prot_length, 186)
        self.assertEqual(effects_sorted[0].aa_change, None)
        self.assertEqual(effects_sorted[0].which_intron, 3)
        self.assertEqual(effects_sorted[0].how_many_introns, 3)
        self.assertEqual(effects_sorted[0].dist_from_coding, 2913)
        self.assertEqual(effects_sorted[0].dist_from_acceptor, 2913)
        self.assertEqual(effects_sorted[0].dist_from_donor, 3504)
        self.assertEqual(effects_sorted[0].intron_length, 6420)

        self.assertEqual(effects_sorted[1].gene, "KDELR2")
        self.assertEqual(effects_sorted[1].transcript_id, "NM_006854_1")
        self.assertEqual(effects_sorted[1].strand, "-")
        self.assertEqual(effects_sorted[1].effect, "no-frame-shift")
        self.assertEqual(effects_sorted[1].prot_pos, 195)
        self.assertEqual(effects_sorted[1].prot_length, 212)
        self.assertEqual(effects_sorted[1].aa_change, "Phe,Tyr->Tyr")

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
        self.assertEqual(effect.aa_change, "->Ser")

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
        self.assertEqual(effect.aa_change, "Ala->Ala,Ala,Ala,Ala,Ala,Ala,Ala")
    #
    # def test_chr21_11097543_del_var(self):
    #     effects = VariantAnnotation.annotate_variant(self.gmDB, self.GA,
    #                                                  loc="21:11097543",
    #                                                  var="del(2)")
    #     self.assertEqual(len(effects), 5)
    #     effects_sorted = sorted(effects, key=lambda k: k.transcript_id)
    #
    #     self.assertEqual(effects_sorted[0].gene, "BAGE")
    #     self.assertEqual(effects_sorted[0].transcript_id, "NM_001187_1")
    #     self.assertEqual(effects_sorted[0].strand, "-")
    #     self.assertEqual(effects_sorted[0].effect, "frame-shift")
    #     # self.assertEqual(effects_sorted[0].prot_pos, 40)
    #     # self.assertEqual(effects_sorted[0].prot_length, 39)
    #     self.assertEqual(effects_sorted[0].aa_change, None)
    #
    #     self.assertEqual(effects_sorted[1].gene, "BAGE4")
    #     self.assertEqual(effects_sorted[1].transcript_id, "NM_181704_1")
    #     self.assertEqual(effects_sorted[1].strand, "-")
    #     self.assertEqual(effects_sorted[1].effect, "noEnd")
    #     # self.assertEqual(effects_sorted[1].prot_pos, 40)
    #     # self.assertEqual(effects_sorted[1].prot_length, 40)
    #     self.assertEqual(effects_sorted[1].aa_change, None)
    #
    #     self.assertEqual(effects_sorted[2].gene, "BAGE3")
    #     self.assertEqual(effects_sorted[2].transcript_id, "NM_182481_1")
    #     self.assertEqual(effects_sorted[2].strand, "-")
    #     self.assertEqual(effects_sorted[2].effect, "splice-site")
    #     # self.assertEqual(effects_sorted[2].prot_pos, 39)
    #     # self.assertEqual(effects_sorted[2].prot_length, 110)
    #     self.assertEqual(effects_sorted[2].aa_change, None)
    #
    #     self.assertEqual(effects_sorted[3].gene, "BAGE2")
    #     self.assertEqual(effects_sorted[3].transcript_id, "NM_182482_1")
    #     self.assertEqual(effects_sorted[3].strand, "-")
    #     self.assertEqual(effects_sorted[3].effect, "splice-site")
    #     # self.assertEqual(effects_sorted[3].prot_pos, 39)
    #     # self.assertEqual(effects_sorted[3].prot_length, 110)
    #     self.assertEqual(effects_sorted[3].aa_change, None)
    #
    #     self.assertEqual(effects_sorted[4].gene, "BAGE5")
    #     self.assertEqual(effects_sorted[4].transcript_id, "NM_182484_1")
    #     self.assertEqual(effects_sorted[4].strand, "-")
    #     self.assertEqual(effects_sorted[4].effect, "frame-shift")
    #     # self.assertEqual(effects_sorted[4].prot_pos, 40)
    #     # self.assertEqual(effects_sorted[4].prot_length, 39)
    #     self.assertEqual(effects_sorted[4].aa_change, None)

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
        self.assertEqual(effects_sorted[0].prot_pos, 83)
        self.assertEqual(effects_sorted[0].prot_length, 594)
        self.assertEqual(effects_sorted[0].aa_change, None)
        self.assertEqual(effects_sorted[0].which_intron, 4)
        self.assertEqual(effects_sorted[0].how_many_introns, 18)
        self.assertEqual(effects_sorted[0].dist_from_coding, 0)
        self.assertEqual(effects_sorted[0].dist_from_acceptor, 0)
        self.assertEqual(effects_sorted[0].dist_from_donor, 1577)
        self.assertEqual(effects_sorted[0].intron_length, 1578)

        self.assertEqual(effects_sorted[1].gene, "STXBP1")
        self.assertEqual(effects_sorted[1].transcript_id, "NM_003165_1")
        self.assertEqual(effects_sorted[1].strand, "+")
        self.assertEqual(effects_sorted[1].effect, "splice-site")
        self.assertEqual(effects_sorted[1].prot_pos, 83)
        self.assertEqual(effects_sorted[1].prot_length, 603)
        self.assertEqual(effects_sorted[1].aa_change, None)
        self.assertEqual(effects_sorted[1].which_intron, 4)
        self.assertEqual(effects_sorted[1].how_many_introns, 19)
        self.assertEqual(effects_sorted[1].dist_from_coding, 0)
        self.assertEqual(effects_sorted[1].dist_from_acceptor, 0)
        self.assertEqual(effects_sorted[1].dist_from_donor, 1577)
        self.assertEqual(effects_sorted[1].intron_length, 1578)

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
        self.assertEqual(effects_sorted[0].prot_length, 806)
        self.assertEqual(effects_sorted[0].aa_change, None)
        self.assertEqual(effects_sorted[1].which_intron, 9)
        self.assertEqual(effects_sorted[1].how_many_introns, 13)
        self.assertEqual(effects_sorted[1].dist_from_coding, -6)
        self.assertEqual(effects_sorted[1].dist_from_acceptor, -6)
        self.assertEqual(effects_sorted[1].dist_from_donor, 98)
        self.assertEqual(effects_sorted[1].intron_length, 102)

        self.assertEqual(effects_sorted[1].gene, "HNRNPU")
        self.assertEqual(effects_sorted[1].transcript_id, "NM_031844_1")
        self.assertEqual(effects_sorted[1].strand, "-")
        self.assertEqual(effects_sorted[1].effect, "splice-site")
        self.assertEqual(effects_sorted[1].prot_pos, 582)
        self.assertEqual(effects_sorted[1].prot_length, 825)
        self.assertEqual(effects_sorted[1].aa_change, None)
        self.assertEqual(effects_sorted[1].which_intron, 9)
        self.assertEqual(effects_sorted[1].how_many_introns, 13)
        self.assertEqual(effects_sorted[1].dist_from_coding, -6)
        self.assertEqual(effects_sorted[1].dist_from_acceptor, -6)
        self.assertEqual(effects_sorted[1].dist_from_donor, 98)
        self.assertEqual(effects_sorted[1].intron_length, 102)

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
        self.assertEqual(effect.aa_change, "Gln->Gln,Glu,Glu")

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
        self.assertEqual(effects_sorted[3].prot_length, 626)
        self.assertEqual(effects_sorted[3].aa_change, None)

        self.assertEqual(effects_sorted[4].gene, "GNAS")
        self.assertEqual(effects_sorted[4].transcript_id, "NM_016592_1")
        self.assertEqual(effects_sorted[4].strand, "+")
        self.assertEqual(effects_sorted[4].effect, "3'UTR-intron")
        self.assertEqual(effects_sorted[4].prot_pos, None)
        self.assertEqual(effects_sorted[4].prot_length, 245)
        self.assertEqual(effects_sorted[4].aa_change, None)

        self.assertEqual(effects_sorted[5].gene, "GNAS")
        self.assertEqual(effects_sorted[5].transcript_id, "NM_080425_1")
        self.assertEqual(effects_sorted[5].strand, "+")
        self.assertEqual(effects_sorted[5].effect, "intron")
        self.assertEqual(effects_sorted[5].prot_pos, 690)
        self.assertEqual(effects_sorted[5].prot_length, 1037)
        self.assertEqual(effects_sorted[5].aa_change, None)
        self.assertEqual(effects_sorted[5].which_intron, 1)
        self.assertEqual(effects_sorted[5].how_many_introns, 12)
        self.assertEqual(effects_sorted[5].dist_from_coding, 3843)
        self.assertEqual(effects_sorted[5].dist_from_acceptor, 3843)
        self.assertEqual(effects_sorted[5].dist_from_donor, 36434)
        self.assertEqual(effects_sorted[5].intron_length, 40278)

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
        self.assertEqual(effects_sorted[0].prot_length, 389)
        self.assertEqual(effects_sorted[0].aa_change, None)
        self.assertEqual(effects_sorted[0].which_intron, 10)
        self.assertEqual(effects_sorted[0].how_many_introns, 11)
        self.assertEqual(effects_sorted[0].dist_from_coding, 0)
        self.assertEqual(effects_sorted[0].dist_from_acceptor, 0)
        self.assertEqual(effects_sorted[0].dist_from_donor, 0)
        self.assertEqual(effects_sorted[0].intron_length, 1)

        self.assertEqual(effects_sorted[1].gene, "RHBG")
        self.assertEqual(effects_sorted[1].transcript_id, "NM_001256396_1")
        self.assertEqual(effects_sorted[1].strand, "+")
        self.assertEqual(effects_sorted[1].effect, "splice-site")
        self.assertEqual(effects_sorted[1].prot_pos, 392)
        self.assertEqual(effects_sorted[1].prot_length, 428)
        self.assertEqual(effects_sorted[1].aa_change, None)
        self.assertEqual(effects_sorted[1].which_intron, 10)
        self.assertEqual(effects_sorted[1].how_many_introns, 11)
        self.assertEqual(effects_sorted[1].dist_from_coding, 0)
        self.assertEqual(effects_sorted[1].dist_from_acceptor, 0)
        self.assertEqual(effects_sorted[1].dist_from_donor, 0)
        self.assertEqual(effects_sorted[1].intron_length, 1)

        self.assertEqual(effects_sorted[2].gene, "RHBG")
        self.assertEqual(effects_sorted[2].transcript_id, "NM_020407_1")
        self.assertEqual(effects_sorted[2].strand, "+")
        self.assertEqual(effects_sorted[2].effect, "splice-site")
        self.assertEqual(effects_sorted[2].prot_pos, 422)
        self.assertEqual(effects_sorted[2].prot_length, 458)
        self.assertEqual(effects_sorted[2].aa_change, None)
        self.assertEqual(effects_sorted[2].which_intron, 9)
        self.assertEqual(effects_sorted[2].how_many_introns, 10)
        self.assertEqual(effects_sorted[2].dist_from_coding, 0)
        self.assertEqual(effects_sorted[2].dist_from_acceptor, 0)
        self.assertEqual(effects_sorted[2].dist_from_donor, 0)
        self.assertEqual(effects_sorted[2].intron_length, 1)

        self.assertEqual(effects_sorted[3].gene, "RHBG")
        self.assertEqual(effects_sorted[3].transcript_id, "NR_046115_1")
        self.assertEqual(effects_sorted[3].strand, "+")
        self.assertEqual(effects_sorted[3].effect, "non-coding")
        self.assertEqual(effects_sorted[3].prot_pos, None)
        self.assertEqual(effects_sorted[3].prot_length, None)
        self.assertEqual(effects_sorted[3].aa_change, None)

    def test_chr17_76528711_sub_var(self):
        [effect] = VariantAnnotation.annotate_variant(self.gmDB, self.GA,
                                                      loc="17:76528711",
                                                      var="sub(C->T)")

        self.assertEqual(effect.gene, "DNAH17")
        self.assertEqual(effect.transcript_id, "NM_173628_1")
        self.assertEqual(effect.strand, "-")
        self.assertEqual(effect.effect, "synonymous")
        self.assertEqual(effect.prot_pos, 989)
        self.assertEqual(effect.prot_length, 4462)
        self.assertEqual(effect.aa_change, "Arg->Arg")

    def test_chr1_244816618_ins_var(self):
        [effect] = VariantAnnotation.annotate_variant(self.gmDB, self.GA,
                                                      loc="1:244816618",
                                                      var="ins(G)")

        self.assertEqual(effect.gene, "DESI2")
        self.assertEqual(effect.transcript_id, "NM_016076_1")
        self.assertEqual(effect.strand, "+")
        self.assertEqual(effect.effect, "noStart")
        self.assertEqual(effect.prot_pos, 1)
        self.assertEqual(effect.prot_length, 194)
        self.assertEqual(effect.aa_change, None)

    def test_chr10_46248650_del_var(self):
        effects = VariantAnnotation.annotate_variant(self.gmDB, self.GA,
                                                     loc="10:46248650",
                                                     var="del(3)")
        self.assertEqual(len(effects), 3)
        effects_sorted = sorted(effects, key=lambda k: k.transcript_id)

        self.assertEqual(effects_sorted[0].gene, "FAM21C")
        self.assertEqual(effects_sorted[0].transcript_id, "NM_001169106_1")
        self.assertEqual(effects_sorted[0].strand, "+")
        self.assertEqual(effects_sorted[0].effect, "no-frame-shift-newStop")
        self.assertEqual(effects_sorted[0].prot_pos, 382)
        self.assertEqual(effects_sorted[0].prot_length, 1279)
        self.assertEqual(effects_sorted[0].aa_change, "Ser,Gln->End")

        self.assertEqual(effects_sorted[1].gene, "FAM21C")
        self.assertEqual(effects_sorted[1].transcript_id, "NM_001169107_1")
        self.assertEqual(effects_sorted[1].strand, "+")
        self.assertEqual(effects_sorted[1].effect, "no-frame-shift-newStop")
        self.assertEqual(effects_sorted[1].prot_pos, 358)
        self.assertEqual(effects_sorted[1].prot_length, 1245)
        self.assertEqual(effects_sorted[1].aa_change, "Ser,Gln->End")

        self.assertEqual(effects_sorted[2].gene, "FAM21C")
        self.assertEqual(effects_sorted[2].transcript_id, "NM_015262_1")
        self.assertEqual(effects_sorted[2].strand, "+")
        self.assertEqual(effects_sorted[2].effect, "no-frame-shift-newStop")
        self.assertEqual(effects_sorted[2].prot_pos, 382)
        self.assertEqual(effects_sorted[2].prot_length, 1320)
        self.assertEqual(effects_sorted[2].aa_change, "Ser,Gln->End")

    def test_chr15_41864763_del_var(self):
        [effect] = VariantAnnotation.annotate_variant(self.gmDB, self.GA,
                                                      loc="15:41864763",
                                                      var="del(3)")

        self.assertEqual(effect.gene, "TYRO3")
        self.assertEqual(effect.transcript_id, "NM_006293_1")
        self.assertEqual(effect.strand, "+")
        self.assertEqual(effect.effect, "splice-site")
        self.assertEqual(effect.prot_pos, 626)
        self.assertEqual(effect.prot_length, 890)
        self.assertEqual(effect.aa_change, None)
        self.assertEqual(effect.which_intron, 15)
        self.assertEqual(effect.how_many_introns, 18)
        self.assertEqual(effect.dist_from_coding, 0)
        self.assertEqual(effect.dist_from_acceptor, 434)
        self.assertEqual(effect.dist_from_donor, 0)
        self.assertEqual(effect.intron_length, 437)

    def test_chr3_131100722_sub_var(self):
        effects = VariantAnnotation.annotate_variant(self.gmDB, self.GA,
                                                     loc="3:131100722",
                                                     var="sub(C->G)")
        self.assertEqual(len(effects), 4)
        effects_sorted = sorted(effects, key=lambda k: k.transcript_id)

        self.assertEqual(effects_sorted[0].gene, "NUDT16")
        self.assertEqual(effects_sorted[0].transcript_id, "NM_001171905_1")
        self.assertEqual(effects_sorted[0].strand, "+")
        self.assertEqual(effects_sorted[0].effect, "5'UTR-intron")
        self.assertEqual(effects_sorted[0].prot_pos, None)
        self.assertEqual(effects_sorted[0].prot_length, 159)
        self.assertEqual(effects_sorted[0].aa_change, None)

        self.assertEqual(effects_sorted[1].gene, "NUDT16")
        self.assertEqual(effects_sorted[1].transcript_id, "NM_001171906_1")
        self.assertEqual(effects_sorted[1].strand, "+")
        self.assertEqual(effects_sorted[1].effect, "missense")
        self.assertEqual(effects_sorted[1].prot_pos, 25)
        self.assertEqual(effects_sorted[1].prot_length, 227)
        self.assertEqual(effects_sorted[1].aa_change, "Ala->Gly")

        self.assertEqual(effects_sorted[2].gene, "NUDT16")
        self.assertEqual(effects_sorted[2].transcript_id, "NM_152395_1")
        self.assertEqual(effects_sorted[2].strand, "+")
        self.assertEqual(effects_sorted[2].effect, "missense")
        self.assertEqual(effects_sorted[2].prot_pos, 25)
        self.assertEqual(effects_sorted[2].prot_length, 195)
        self.assertEqual(effects_sorted[2].aa_change, "Ala->Gly")

        self.assertEqual(effects_sorted[3].gene, "NUDT16")
        self.assertEqual(effects_sorted[3].transcript_id, "NR_033268_1")
        self.assertEqual(effects_sorted[3].strand, "+")
        self.assertEqual(effects_sorted[3].effect, "non-coding")
        self.assertEqual(effects_sorted[3].prot_pos, None)
        self.assertEqual(effects_sorted[3].prot_length, None)
        self.assertEqual(effects_sorted[3].aa_change, None)

    def test_chr1_42619122_sub_var(self):
        [effect] = VariantAnnotation.annotate_variant(self.gmDB, self.GA,
                                                      loc="1:42619122",
                                                      var="sub(A->G)")

        self.assertEqual(effect.gene, "GUCA2B")
        self.assertEqual(effect.transcript_id, "NM_007102_1")
        self.assertEqual(effect.strand, "+")
        self.assertEqual(effect.effect, "noStart")
        self.assertEqual(effect.prot_pos, 1)
        self.assertEqual(effect.prot_length, 112)
        self.assertEqual(effect.aa_change, None)

    def test_chr1_16558543_sub_var(self):
        [effect] = VariantAnnotation.annotate_variant(self.gmDB, self.GA,
                                                      loc="1:16558543",
                                                      var="sub(T->C)")

        self.assertEqual(effect.gene, "RSG1")
        self.assertEqual(effect.transcript_id, "NM_030907_1")
        self.assertEqual(effect.strand, "-")
        self.assertEqual(effect.effect, "noEnd")
        self.assertEqual(effect.prot_pos, 259)
        self.assertEqual(effect.prot_length, 258)
        self.assertEqual(effect.aa_change, None)

    def test_chr1_47515176_ins_var(self):
        [effect] = VariantAnnotation.annotate_variant(self.gmDB, self.GA,
                                                      loc="1:47515176",
                                                      var="ins(TAGAAATATAAT)")

        self.assertEqual(effect.gene, "CYP4X1")
        self.assertEqual(effect.transcript_id, "NM_178033_1")
        self.assertEqual(effect.strand, "+")
        self.assertEqual(effect.effect, "no-frame-shift-newStop")
        self.assertEqual(effect.prot_pos, 452)
        self.assertEqual(effect.prot_length, 509)
        self.assertEqual(effect.aa_change, "Arg->Ile,Glu,Ile,End,Trp")

    def test_chr1_120934555_sub_var(self):
        effects = VariantAnnotation.annotate_variant(self.gmDB, self.GA,
                                                     loc="1:120934555",
                                                     var="sub(C->T)")
        self.assertEqual(len(effects), 4)
        effects_sorted = sorted(effects, key=lambda k: k.transcript_id)

        self.assertEqual(effects_sorted[0].gene, "FCGR1B")
        self.assertEqual(effects_sorted[0].transcript_id, "NM_001004340_1")
        self.assertEqual(effects_sorted[0].strand, "-")
        self.assertEqual(effects_sorted[0].effect, "intron")
        self.assertEqual(effects_sorted[0].prot_pos, 11)
        self.assertEqual(effects_sorted[0].prot_length, 188)
        self.assertEqual(effects_sorted[0].aa_change, None)
        self.assertEqual(effects_sorted[0].which_intron, 1)
        self.assertEqual(effects_sorted[0].how_many_introns, 2)
        self.assertEqual(effects_sorted[0].dist_from_coding, 1308)
        self.assertEqual(effects_sorted[0].dist_from_acceptor, 4261)
        self.assertEqual(effects_sorted[0].dist_from_donor, 1308)
        self.assertEqual(effects_sorted[0].intron_length, 5570)

        self.assertEqual(effects_sorted[1].gene, "FCGR1B")
        self.assertEqual(effects_sorted[1].transcript_id, "NM_001017986_1")
        self.assertEqual(effects_sorted[1].strand, "-")
        self.assertEqual(effects_sorted[1].effect, "missense")
        self.assertEqual(effects_sorted[1].prot_pos, 45)
        self.assertEqual(effects_sorted[1].prot_length, 280)
        self.assertEqual(effects_sorted[1].aa_change, "Val->Met")

        self.assertEqual(effects_sorted[2].gene, "FCGR1B")
        self.assertEqual(effects_sorted[2].transcript_id, "NM_001244910_1")
        self.assertEqual(effects_sorted[2].strand, "-")
        self.assertEqual(effects_sorted[2].effect, "missense")
        self.assertEqual(effects_sorted[2].prot_pos, 45)
        self.assertEqual(effects_sorted[2].prot_length, 224)
        self.assertEqual(effects_sorted[2].aa_change, "Val->Met")

        self.assertEqual(effects_sorted[3].gene, "FCGR1B")
        self.assertEqual(effects_sorted[3].transcript_id, "NR_045213_1")
        self.assertEqual(effects_sorted[3].strand, "-")
        self.assertEqual(effects_sorted[3].effect, "non-coding")
        self.assertEqual(effects_sorted[3].prot_pos, None)
        self.assertEqual(effects_sorted[3].prot_length, None)
        self.assertEqual(effects_sorted[3].aa_change, None)

    def test_chr1_26190329_del_var(self):
        [effect] = VariantAnnotation.annotate_variant(self.gmDB, self.GA,
                                                      loc="1:26190329",
                                                      var="del(6)")

        self.assertEqual(effect.gene, "PAQR7")
        self.assertEqual(effect.transcript_id, "NM_178422_1")
        self.assertEqual(effect.strand, "-")
        self.assertEqual(effect.effect, "noStart")
        self.assertEqual(effect.prot_pos, 1)
        self.assertEqual(effect.prot_length, 346)
        self.assertEqual(effect.aa_change, None)

    def test_chr1_42628578_del_var(self):
        [effect] = VariantAnnotation.annotate_variant(self.gmDB, self.GA,
                                                      loc="1:42628578",
                                                      var="del(1)")

        self.assertEqual(effect.gene, "GUCA2A")
        self.assertEqual(effect.transcript_id, "NM_033553_1")
        self.assertEqual(effect.strand, "-")
        self.assertEqual(effect.effect, "noEnd")
        self.assertEqual(effect.prot_pos, 116)
        self.assertEqual(effect.prot_length, 115)
        self.assertEqual(effect.aa_change, None)

    def test_chr1_203652334_del_var(self):
        effects = VariantAnnotation.annotate_variant(self.gmDB, self.GA,
                                                     loc="1:203652334",
                                                     var="del(6)")
        self.assertEqual(len(effects), 2)
        effects_sorted = sorted(effects, key=lambda k: k.transcript_id)

        self.assertEqual(effects_sorted[0].gene, "ATP2B4")
        self.assertEqual(effects_sorted[0].transcript_id, "NM_001001396_1")
        self.assertEqual(effects_sorted[0].strand, "+")
        self.assertEqual(effects_sorted[0].effect, "noStart")
        self.assertEqual(effects_sorted[0].prot_pos, 1)
        self.assertEqual(effects_sorted[0].prot_length, 1170)
        self.assertEqual(effects_sorted[0].aa_change, None)

        self.assertEqual(effects_sorted[1].gene, "ATP2B4")
        self.assertEqual(effects_sorted[1].transcript_id, "NM_001684_1")
        self.assertEqual(effects_sorted[1].strand, "+")
        self.assertEqual(effects_sorted[1].effect, "noStart")
        self.assertEqual(effects_sorted[1].prot_pos, 1)
        self.assertEqual(effects_sorted[1].prot_length, 1205)
        self.assertEqual(effects_sorted[1].aa_change, None)

    def test_chr2_133426005_del_var(self):
        effects = VariantAnnotation.annotate_variant(self.gmDB, self.GA,
                                                     loc="2:133426005",
                                                     var="del(2)")
        self.assertEqual(len(effects), 2)
        effects_sorted = sorted(effects, key=lambda k: k.transcript_id)

        self.assertEqual(effects_sorted[0].gene, "LYPD1")
        self.assertEqual(effects_sorted[0].transcript_id, "NM_001077427_1")
        self.assertEqual(effects_sorted[0].strand, "-")
        self.assertEqual(effects_sorted[0].effect, "noStart")
        self.assertEqual(effects_sorted[0].prot_pos, 1)
        self.assertEqual(effects_sorted[0].prot_length, 89)
        self.assertEqual(effects_sorted[0].aa_change, None)

        self.assertEqual(effects_sorted[1].gene, "LYPD1")
        self.assertEqual(effects_sorted[1].transcript_id, "NM_144586_1")
        self.assertEqual(effects_sorted[1].strand, "-")
        self.assertEqual(effects_sorted[1].effect, "frame-shift")
        self.assertEqual(effects_sorted[1].prot_pos, 53)
        self.assertEqual(effects_sorted[1].prot_length, 141)
        # self.assertEqual(effects_sorted[1].aa_change, None)

    def test_chr1_237060943_ins_var(self):
        [effect] = VariantAnnotation.annotate_variant(self.gmDB, self.GA,
                                                      loc="1:237060943",
                                                      var="ins(TTTGGAATAG)")

        self.assertEqual(effect.gene, "MTR")
        self.assertEqual(effect.transcript_id, "NM_000254_1")
        self.assertEqual(effect.strand, "+")
        self.assertEqual(effect.effect, "noEnd")
        self.assertEqual(effect.prot_pos, 1266)
        self.assertEqual(effect.prot_length, 1265)
        self.assertEqual(effect.aa_change, None)

    def test_chr1_160854666_ins_var(self):
        [effect] = VariantAnnotation.annotate_variant(self.gmDB, self.GA,
                                                      loc="1:160854666",
                                                      var="ins(AA)")

        self.assertEqual(effect.gene, "ITLN1")
        self.assertEqual(effect.transcript_id, "NM_017625_1")
        self.assertEqual(effect.strand, "-")
        self.assertEqual(effect.effect, "noStart")
        self.assertEqual(effect.prot_pos, 1)
        self.assertEqual(effect.prot_length, 313)
        self.assertEqual(effect.aa_change, None)

    def test_chr1_248903150_ins_var(self):
        var = "ins(AGTCTAGGCAATCTTCCCAGAATGGAAACCCAATCCACTCTTACTA)"
        [effect] = VariantAnnotation.annotate_variant(self.gmDB, self.GA,
                                                      loc="1:248903150",
                                                      var=var)

        self.assertEqual(effect.gene, "LYPD8")
        self.assertEqual(effect.transcript_id, "NM_001085474_1")
        self.assertEqual(effect.strand, "-")
        self.assertEqual(effect.effect, "noStart")
        self.assertEqual(effect.prot_pos, 1)
        self.assertEqual(effect.prot_length, 79)
        self.assertEqual(effect.aa_change, None)

    def test_chr2_58390000_del_var(self):
        effects = VariantAnnotation.annotate_variant(self.gmDB, self.GA,
                                                     loc="2:58390000",
                                                     var="del(1)")
        self.assertEqual(len(effects), 2)
        effects_sorted = sorted(effects, key=lambda k: k.transcript_id)

        self.assertEqual(effects_sorted[0].gene, "FANCL")
        self.assertEqual(effects_sorted[0].transcript_id, "NM_001114636_1")
        self.assertEqual(effects_sorted[0].strand, "-")
        self.assertEqual(effects_sorted[0].effect, "splice-site")
        self.assertEqual(effects_sorted[0].prot_pos, 307)
        self.assertEqual(effects_sorted[0].prot_length, 380)
        self.assertEqual(effects_sorted[0].aa_change, None)
        self.assertEqual(effects_sorted[0].which_intron, 11)
        self.assertEqual(effects_sorted[0].how_many_introns, 13)
        self.assertEqual(effects_sorted[0].dist_from_coding, 0)
        self.assertEqual(effects_sorted[0].dist_from_acceptor, 1226)
        self.assertEqual(effects_sorted[0].dist_from_donor, 0)
        self.assertEqual(effects_sorted[0].intron_length, 1227)

        self.assertEqual(effects_sorted[1].gene, "FANCL")
        self.assertEqual(effects_sorted[1].transcript_id, "NM_018062_1")
        self.assertEqual(effects_sorted[1].strand, "-")
        self.assertEqual(effects_sorted[1].effect, "splice-site")
        self.assertEqual(effects_sorted[1].prot_pos, 302)
        self.assertEqual(effects_sorted[1].prot_length, 375)
        self.assertEqual(effects_sorted[1].aa_change, None)
        self.assertEqual(effects_sorted[1].which_intron, 11)
        self.assertEqual(effects_sorted[1].how_many_introns, 13)
        self.assertEqual(effects_sorted[1].dist_from_coding, 0)
        self.assertEqual(effects_sorted[1].dist_from_acceptor, 1226)
        self.assertEqual(effects_sorted[1].dist_from_donor, 0)
        self.assertEqual(effects_sorted[1].intron_length, 1227)

    def test_chr20_5295014_ins_var(self):
        [effect] = VariantAnnotation.annotate_variant(self.gmDB, self.GA,
                                                      loc="20:5295014",
                                                      var="ins(AAG)")

        self.assertEqual(effect.gene, "PROKR2")
        self.assertEqual(effect.transcript_id, "NM_144773_1")
        self.assertEqual(effect.strand, "-")
        self.assertEqual(effect.effect, "noStart")
        self.assertEqual(effect.prot_pos, 1)
        self.assertEqual(effect.prot_length, 384)
        self.assertEqual(effect.aa_change, None)

    def test_chr5_126859172_del_var(self):
        [effect] = VariantAnnotation.annotate_variant(self.gmDB, self.GA,
                                                      loc="5:126859172",
                                                      var="del(3)")

        self.assertEqual(effect.gene, "PRRC1")
        self.assertEqual(effect.transcript_id, "NM_130809_1")
        self.assertEqual(effect.strand, "+")
        self.assertEqual(effect.effect, "noStart")
        self.assertEqual(effect.prot_pos, 1)
        self.assertEqual(effect.prot_length, 445)
        self.assertEqual(effect.aa_change, None)

    def test_chr4_141471529_ins_var(self):
        [effect] = VariantAnnotation.annotate_variant(self.gmDB, self.GA,
                                                      loc="4:141471529",
                                                      var="ins(T)")

        self.assertEqual(effect.gene, "ELMOD2")
        self.assertEqual(effect.transcript_id, "NM_153702_1")
        self.assertEqual(effect.strand, "+")
        self.assertEqual(effect.effect, "noEnd")
        self.assertEqual(effect.prot_pos, 294)
        self.assertEqual(effect.prot_length, 293)
        self.assertEqual(effect.aa_change, None)

    def test_chr1_33330213_del_var(self):
        effects = VariantAnnotation.annotate_variant(self.gmDB, self.GA,
                                                     loc="1:33330213",
                                                     var="del(1)")
        self.assertEqual(len(effects), 3)
        effects_sorted = sorted(effects, key=lambda k: k.transcript_id)

        self.assertEqual(effects_sorted[0].gene, "FNDC5")
        self.assertEqual(effects_sorted[0].transcript_id, "NM_001171940_1")
        self.assertEqual(effects_sorted[0].strand, "-")
        self.assertEqual(effects_sorted[0].effect, "intron")
        self.assertEqual(effects_sorted[0].prot_pos, 178)
        self.assertEqual(effects_sorted[0].prot_length, 181)
        self.assertEqual(effects_sorted[0].aa_change, None)
        self.assertEqual(effects_sorted[0].which_intron, 5)
        self.assertEqual(effects_sorted[0].how_many_introns, 5)
        self.assertEqual(effects_sorted[0].dist_from_coding, 153)
        self.assertEqual(effects_sorted[0].dist_from_acceptor, 859)
        self.assertEqual(effects_sorted[0].dist_from_donor, 153)
        self.assertEqual(effects_sorted[0].intron_length, 1013)

        self.assertEqual(effects_sorted[1].gene, "FNDC5")
        self.assertEqual(effects_sorted[1].transcript_id, "NM_001171941_1")
        self.assertEqual(effects_sorted[1].strand, "-")
        self.assertEqual(effects_sorted[1].effect, "noEnd")
        self.assertEqual(effects_sorted[1].prot_pos, 154)
        self.assertEqual(effects_sorted[1].prot_length, 153)
        self.assertEqual(effects_sorted[1].aa_change, None)

        self.assertEqual(effects_sorted[2].gene, "FNDC5")
        self.assertEqual(effects_sorted[2].transcript_id, "NM_153756_1")
        self.assertEqual(effects_sorted[2].strand, "-")
        self.assertEqual(effects_sorted[2].effect, "intron")
        self.assertEqual(effects_sorted[2].prot_pos, 212)
        self.assertEqual(effects_sorted[2].prot_length, 212)
        self.assertEqual(effects_sorted[2].aa_change, None)
        self.assertEqual(effects_sorted[2].which_intron, 5)
        self.assertEqual(effects_sorted[2].how_many_introns, 5)
        self.assertEqual(effects_sorted[2].dist_from_coding, 51)
        self.assertEqual(effects_sorted[2].dist_from_acceptor, 312)
        self.assertEqual(effects_sorted[2].dist_from_donor, 51)
        self.assertEqual(effects_sorted[2].intron_length, 364)

    def test_chr5_96430453_ins_var(self):
        [effect] = VariantAnnotation.annotate_variant(self.gmDB, self.GA,
                                                      loc="5:96430453",
                                                      var="ins(TAG)")

        self.assertEqual(effect.gene, "LIX1")
        self.assertEqual(effect.transcript_id, "NM_153234_1")
        self.assertEqual(effect.strand, "-")
        self.assertEqual(effect.effect, "noEnd")
        self.assertEqual(effect.prot_pos, 283)
        self.assertEqual(effect.prot_length, 282)
        self.assertEqual(effect.aa_change, None)

    def test_chr10_25138774_ins_var(self):
        var = "ins(ATATTGGATTTAATCCAAGTTAACAAAAATAAAGCCGCAGGA)"
        [effect] = VariantAnnotation.annotate_variant(self.gmDB, self.GA,
                                                      loc="10:25138774",
                                                      var=var)

        self.assertEqual(effect.gene, "PRTFDC1")
        self.assertEqual(effect.transcript_id, "NM_020200_1")
        self.assertEqual(effect.strand, "-")
        self.assertEqual(effect.effect, "noEnd")
        self.assertEqual(effect.prot_pos, 226)
        self.assertEqual(effect.prot_length, 225)
        self.assertEqual(effect.aa_change, None)

    def test_chr2_218747134_ins_var(self):
        [effect] = VariantAnnotation.annotate_variant(self.gmDB, self.GA,
                                                      loc="2:218747134",
                                                      var="ins(AGTTAT)")

        self.assertEqual(effect.gene, "TNS1")
        self.assertEqual(effect.transcript_id, "NM_022648_1")
        self.assertEqual(effect.strand, "-")
        self.assertEqual(effect.effect, "no-frame-shift-newStop")
        self.assertEqual(effect.prot_pos, 291)
        self.assertEqual(effect.prot_length, 1735)
        self.assertEqual(effect.aa_change, "Asp->Glu,End,Leu")

    def test_chr11_3846347_del_var(self):
        effects = VariantAnnotation.annotate_variant(self.gmDB, self.GA,
                                                     loc="11:3846347",
                                                     var="del(12)")
        self.assertEqual(len(effects), 16)
        effects_sorted = sorted(effects, key=lambda k: k.transcript_id)

        self.assertEqual(effects_sorted[0].gene, "PGAP2")
        self.assertEqual(effects_sorted[0].transcript_id, "NM_001145438_1")
        self.assertEqual(effects_sorted[0].strand, "+")
        self.assertEqual(effects_sorted[0].effect, "no-frame-shift")
        self.assertEqual(effects_sorted[0].prot_pos, 261)
        self.assertEqual(effects_sorted[0].prot_length, 307)
        self.assertEqual(effects_sorted[0].aa_change, "Cys,Glu,Ala,Gly,Val"
                                                      "->Leu")

        self.assertEqual(effects_sorted[1].gene, "PGAP2")
        self.assertEqual(effects_sorted[1].transcript_id, "NM_001256235_1")
        self.assertEqual(effects_sorted[1].strand, "+")
        self.assertEqual(effects_sorted[1].effect, "no-frame-shift")
        self.assertEqual(effects_sorted[1].prot_pos, 226)
        self.assertEqual(effects_sorted[1].prot_length, 272)
        self.assertEqual(effects_sorted[1].aa_change, "Cys,Glu,Ala,Gly,Val"
                                                      "->Leu")

        self.assertEqual(effects_sorted[2].gene, "PGAP2")
        self.assertEqual(effects_sorted[2].transcript_id, "NM_001256236_1")
        self.assertEqual(effects_sorted[2].strand, "+")
        self.assertEqual(effects_sorted[2].effect, "no-frame-shift")
        self.assertEqual(effects_sorted[2].prot_pos, 326)
        self.assertEqual(effects_sorted[2].prot_length, 372)
        self.assertEqual(effects_sorted[2].aa_change, "Cys,Glu,Ala,Gly,Val"
                                                      "->Leu")

        self.assertEqual(effects_sorted[3].gene, "PGAP2")
        self.assertEqual(effects_sorted[3].transcript_id, "NM_001256237_1")
        self.assertEqual(effects_sorted[3].strand, "+")
        self.assertEqual(effects_sorted[3].effect, "noEnd")
        self.assertEqual(effects_sorted[3].prot_pos, 291)
        self.assertEqual(effects_sorted[3].prot_length, 291)
        self.assertEqual(effects_sorted[3].aa_change, None)

        self.assertEqual(effects_sorted[4].gene, "PGAP2")
        self.assertEqual(effects_sorted[4].transcript_id, "NM_001256238_1")
        self.assertEqual(effects_sorted[4].strand, "+")
        self.assertEqual(effects_sorted[4].effect, "noEnd")
        self.assertEqual(effects_sorted[4].prot_pos, 232)
        self.assertEqual(effects_sorted[4].prot_length, 232)
        self.assertEqual(effects_sorted[4].aa_change, None)

        self.assertEqual(effects_sorted[5].gene, "PGAP2")
        self.assertEqual(effects_sorted[5].transcript_id, "NM_001256239_1")
        self.assertEqual(effects_sorted[5].strand, "+")
        self.assertEqual(effects_sorted[5].effect, "no-frame-shift")
        self.assertEqual(effects_sorted[5].prot_pos, 204)
        self.assertEqual(effects_sorted[5].prot_length, 250)
        self.assertEqual(effects_sorted[5].aa_change, "Cys,Glu,Ala,Gly,Val"
                                                      "->Leu")

        self.assertEqual(effects_sorted[6].gene, "PGAP2")
        self.assertEqual(effects_sorted[6].transcript_id, "NM_001256240_1")
        self.assertEqual(effects_sorted[6].strand, "+")
        self.assertEqual(effects_sorted[6].effect, "no-frame-shift")
        self.assertEqual(effects_sorted[6].prot_pos, 208)
        self.assertEqual(effects_sorted[6].prot_length, 254)
        self.assertEqual(effects_sorted[6].aa_change, "Cys,Glu,Ala,Gly,Val"
                                                      "->Leu")

        self.assertEqual(effects_sorted[7].gene, "PGAP2")
        self.assertEqual(effects_sorted[7].transcript_id, "NM_014489_1")
        self.assertEqual(effects_sorted[7].strand, "+")
        self.assertEqual(effects_sorted[7].effect, "no-frame-shift")
        self.assertEqual(effects_sorted[7].prot_pos, 269)
        self.assertEqual(effects_sorted[7].prot_length, 315)
        self.assertEqual(effects_sorted[7].aa_change, "Cys,Glu,Ala,Gly,Val"
                                                      "->Leu")

        self.assertEqual(effects_sorted[8].gene, "PGAP2")
        self.assertEqual(effects_sorted[8].transcript_id, "NR_027016_1")
        self.assertEqual(effects_sorted[8].strand, "+")
        self.assertEqual(effects_sorted[8].effect, "non-coding")
        self.assertEqual(effects_sorted[8].prot_pos, None)
        self.assertEqual(effects_sorted[8].prot_length, None)
        self.assertEqual(effects_sorted[8].aa_change, None)

        self.assertEqual(effects_sorted[9].gene, "PGAP2")
        self.assertEqual(effects_sorted[9].transcript_id, "NR_027017_1")
        self.assertEqual(effects_sorted[9].strand, "+")
        self.assertEqual(effects_sorted[9].effect, "non-coding")
        self.assertEqual(effects_sorted[9].prot_pos, None)
        self.assertEqual(effects_sorted[9].prot_length, None)
        self.assertEqual(effects_sorted[9].aa_change, None)

        self.assertEqual(effects_sorted[10].gene, "PGAP2")
        self.assertEqual(effects_sorted[10].transcript_id, "NR_027018_1")
        self.assertEqual(effects_sorted[10].strand, "+")
        self.assertEqual(effects_sorted[10].effect, "non-coding")
        self.assertEqual(effects_sorted[10].prot_pos, None)
        self.assertEqual(effects_sorted[10].prot_length, None)
        self.assertEqual(effects_sorted[10].aa_change, None)

        self.assertEqual(effects_sorted[11].gene, "PGAP2")
        self.assertEqual(effects_sorted[11].transcript_id, "NR_045923_1")
        self.assertEqual(effects_sorted[11].strand, "+")
        self.assertEqual(effects_sorted[11].effect, "non-coding")
        self.assertEqual(effects_sorted[11].prot_pos, None)
        self.assertEqual(effects_sorted[11].prot_length, None)
        self.assertEqual(effects_sorted[11].aa_change, None)

        self.assertEqual(effects_sorted[12].gene, "PGAP2")
        self.assertEqual(effects_sorted[12].transcript_id, "NR_045925_1")
        self.assertEqual(effects_sorted[12].strand, "+")
        self.assertEqual(effects_sorted[12].effect, "non-coding")
        self.assertEqual(effects_sorted[12].prot_pos, None)
        self.assertEqual(effects_sorted[12].prot_length, None)
        self.assertEqual(effects_sorted[12].aa_change, None)

        self.assertEqual(effects_sorted[13].gene, "PGAP2")
        self.assertEqual(effects_sorted[13].transcript_id, "NR_045926_1")
        self.assertEqual(effects_sorted[13].strand, "+")
        self.assertEqual(effects_sorted[13].effect, "non-coding")
        self.assertEqual(effects_sorted[13].prot_pos, None)
        self.assertEqual(effects_sorted[13].prot_length, None)
        self.assertEqual(effects_sorted[13].aa_change, None)

        self.assertEqual(effects_sorted[14].gene, "PGAP2")
        self.assertEqual(effects_sorted[14].transcript_id, "NR_045927_1")
        self.assertEqual(effects_sorted[14].strand, "+")
        self.assertEqual(effects_sorted[14].effect, "non-coding")
        self.assertEqual(effects_sorted[14].prot_pos, None)
        self.assertEqual(effects_sorted[14].prot_length, None)
        self.assertEqual(effects_sorted[14].aa_change, None)

        self.assertEqual(effects_sorted[15].gene, "PGAP2")
        self.assertEqual(effects_sorted[15].transcript_id, "NR_045929_1")
        self.assertEqual(effects_sorted[15].strand, "+")
        self.assertEqual(effects_sorted[15].effect, "non-coding")
        self.assertEqual(effects_sorted[15].prot_pos, None)
        self.assertEqual(effects_sorted[15].prot_length, None)
        self.assertEqual(effects_sorted[15].aa_change, None)

    def test_chr1_145567756_ins_var(self):
        effects = VariantAnnotation.annotate_variant(self.gmDB, self.GA,
                                                     loc="1:145567756",
                                                     var="ins(CTC)")
        self.assertEqual(len(effects), 4)
        effects_sorted = sorted(effects, key=lambda k: k.transcript_id)

        self.assertEqual(effects_sorted[0].gene, "NBPF10")
        self.assertEqual(effects_sorted[0].transcript_id, "NM_001039703_1")
        self.assertEqual(effects_sorted[0].strand, "+")
        self.assertEqual(effects_sorted[0].effect, "intron")
        self.assertEqual(effects_sorted[0].prot_pos, 2872)
        self.assertEqual(effects_sorted[0].prot_length, 3626)
        self.assertEqual(effects_sorted[0].aa_change, None)
        self.assertEqual(effects_sorted[0].which_intron, 68)
        self.assertEqual(effects_sorted[0].how_many_introns, 85)
        self.assertEqual(effects_sorted[0].dist_from_coding, 202296)
        self.assertEqual(effects_sorted[0].dist_from_acceptor, 853155)
        self.assertEqual(effects_sorted[0].dist_from_donor, 202296)
        self.assertEqual(effects_sorted[0].intron_length, 1055451)

        self.assertEqual(effects_sorted[1].gene, "LOC100288142")
        self.assertEqual(effects_sorted[1].transcript_id, "NM_001278267_1")
        self.assertEqual(effects_sorted[1].strand, "+")
        self.assertEqual(effects_sorted[1].effect, "intron")
        self.assertEqual(effects_sorted[1].prot_pos, 3663)
        self.assertEqual(effects_sorted[1].prot_length, 4963)
        self.assertEqual(effects_sorted[1].aa_change, None)
        self.assertEqual(effects_sorted[1].which_intron, 99)
        self.assertEqual(effects_sorted[1].how_many_introns, 130)
        self.assertEqual(effects_sorted[1].dist_from_coding, 203081)
        self.assertEqual(effects_sorted[1].dist_from_acceptor, 852263)
        self.assertEqual(effects_sorted[1].dist_from_donor, 203081)
        self.assertEqual(effects_sorted[1].intron_length, 1055344)

        self.assertEqual(effects_sorted[2].gene, "ANKRD35")
        self.assertEqual(effects_sorted[2].transcript_id, "NM_001280799_1")
        self.assertEqual(effects_sorted[2].strand, "+")
        self.assertEqual(effects_sorted[2].effect, "noEnd")
        self.assertEqual(effects_sorted[2].prot_pos, 912)
        self.assertEqual(effects_sorted[2].prot_length, 911)
        self.assertEqual(effects_sorted[2].aa_change, None)

        self.assertEqual(effects_sorted[3].gene, "ANKRD35")
        self.assertEqual(effects_sorted[3].transcript_id, "NM_144698_1")
        self.assertEqual(effects_sorted[3].strand, "+")
        self.assertEqual(effects_sorted[3].effect, "noEnd")
        self.assertEqual(effects_sorted[3].prot_pos, 1002)
        self.assertEqual(effects_sorted[3].prot_length, 1001)
        self.assertEqual(effects_sorted[3].aa_change, None)

    def test_chr3_135969219_ins_var(self):
        var = "ins(TGGCGGCGGCATTACGGG)"
        effects = VariantAnnotation.annotate_variant(self.gmDB, self.GA,
                                                     loc="3:135969219",
                                                     var=var)
        self.assertEqual(len(effects), 2)
        effects_sorted = sorted(effects, key=lambda k: k.transcript_id)

        self.assertEqual(effects_sorted[0].gene, "PCCB")
        self.assertEqual(effects_sorted[0].transcript_id, "NM_000532_1")
        self.assertEqual(effects_sorted[0].strand, "+")
        self.assertEqual(effects_sorted[0].effect, "noStart")
        self.assertEqual(effects_sorted[0].prot_pos, 1)
        self.assertEqual(effects_sorted[0].prot_length, 539)
        self.assertEqual(effects_sorted[0].aa_change, None)

        self.assertEqual(effects_sorted[1].gene, "PCCB")
        self.assertEqual(effects_sorted[1].transcript_id, "NM_001178014_1")
        self.assertEqual(effects_sorted[1].strand, "+")
        self.assertEqual(effects_sorted[1].effect, "noStart")
        self.assertEqual(effects_sorted[1].prot_pos, 1)
        self.assertEqual(effects_sorted[1].prot_length, 559)
        self.assertEqual(effects_sorted[1].aa_change, None)

    def test_chr1_27180332_del_var(self):
        [effect] = VariantAnnotation.annotate_variant(self.gmDB, self.GA,
                                                      loc="1:27180332",
                                                      var="del(1)")

        self.assertEqual(effect.gene, "ZDHHC18")
        self.assertEqual(effect.transcript_id, "NM_032283_1")
        self.assertEqual(effect.strand, "+")
        self.assertEqual(effect.effect, "noEnd")
        self.assertEqual(effect.prot_pos, 389)
        self.assertEqual(effect.prot_length, 388)
        self.assertEqual(effect.aa_change, None)

    def test_chr1_1425787_ins_var(self):
        var = "ins(ACGTGACATTTAGCTGTCACTTCTGGTGGGCTCCTGCCA)"
        [effect] = VariantAnnotation.annotate_variant(self.gmDB, self.GA,
                                                      loc="1:1425787",
                                                      var=var)

        self.assertEqual(effect.gene, "ATAD3B")
        self.assertEqual(effect.transcript_id, "NM_031921_1")
        self.assertEqual(effect.strand, "+")
        self.assertEqual(effect.effect, "no-frame-shift-newStop")
        self.assertEqual(effect.prot_pos, 496)
        self.assertEqual(effect.prot_length, 648)
        self.assertEqual(effect.aa_change, "Pro->Pro,Arg,Asp,Ile,End,Leu,Ser,"
                                           "Leu,Leu,Val,Gly,Ser,Cys,Gln")

    def test_chr1_33476432_ins_var(self):
        var = "ins(AGGATGTGGCTTTGGAGA)"
        effects = VariantAnnotation.annotate_variant(self.gmDB, self.GA,
                                                     loc="1:33476432", var=var)
        self.assertEqual(len(effects), 3)
        effects_sorted = sorted(effects, key=lambda k: k.transcript_id)

        self.assertEqual(effects_sorted[0].gene, "AK2")
        self.assertEqual(effects_sorted[0].transcript_id, "NM_001199199_1")
        self.assertEqual(effects_sorted[0].strand, "-")
        self.assertEqual(effects_sorted[0].effect, "noEnd")
        self.assertEqual(effects_sorted[0].prot_pos, 225)
        self.assertEqual(effects_sorted[0].prot_length, 224)
        self.assertEqual(effects_sorted[0].aa_change, None)

        self.assertEqual(effects_sorted[1].gene, "AK2")
        self.assertEqual(effects_sorted[1].transcript_id, "NM_013411_1")
        self.assertEqual(effects_sorted[1].strand, "-")
        self.assertEqual(effects_sorted[1].effect, "noEnd")
        self.assertEqual(effects_sorted[1].prot_pos, 233)
        self.assertEqual(effects_sorted[1].prot_length, 232)
        self.assertEqual(effects_sorted[1].aa_change, None)

        self.assertEqual(effects_sorted[2].gene, "AK2")
        self.assertEqual(effects_sorted[2].transcript_id, "NR_037591_1")
        self.assertEqual(effects_sorted[2].strand, "-")
        self.assertEqual(effects_sorted[2].effect, "non-coding")
        self.assertEqual(effects_sorted[2].prot_pos, None)
        self.assertEqual(effects_sorted[2].prot_length, None)
        self.assertEqual(effects_sorted[2].aa_change, None)

    def test_chr1_245017754_del_var(self):
        effects = VariantAnnotation.annotate_variant(self.gmDB, self.GA,
                                                     loc="1:245017754",
                                                     var="del(3)")
        self.assertEqual(len(effects), 2)
        effects_sorted = sorted(effects, key=lambda k: k.transcript_id)

        self.assertEqual(effects_sorted[0].gene, "HNRNPU")
        self.assertEqual(effects_sorted[0].transcript_id, "NM_004501_1")
        self.assertEqual(effects_sorted[0].strand, "-")
        self.assertEqual(effects_sorted[0].effect, "noEnd")
        self.assertEqual(effects_sorted[0].prot_pos, 806)
        self.assertEqual(effects_sorted[0].prot_length, 806)
        self.assertEqual(effects_sorted[0].aa_change, None)

        self.assertEqual(effects_sorted[1].gene, "HNRNPU")
        self.assertEqual(effects_sorted[1].transcript_id, "NM_031844_1")
        self.assertEqual(effects_sorted[1].strand, "-")
        self.assertEqual(effects_sorted[1].effect, "noEnd")
        self.assertEqual(effects_sorted[1].prot_pos, 825)
        self.assertEqual(effects_sorted[1].prot_length, 825)
        self.assertEqual(effects_sorted[1].aa_change, None)

    def test_chr4_26862842_del_var(self):
        effects = VariantAnnotation.annotate_variant(self.gmDB, self.GA,
                                                     loc="4:26862842",
                                                     var="del(3)")
        self.assertEqual(len(effects), 3)
        effects_sorted = sorted(effects, key=lambda k: k.transcript_id)

        self.assertEqual(effects_sorted[0].gene, "STIM2")
        self.assertEqual(effects_sorted[0].transcript_id, "NM_001169117_1")
        self.assertEqual(effects_sorted[0].strand, "+")
        self.assertEqual(effects_sorted[0].effect, "noStart")
        self.assertEqual(effects_sorted[0].prot_pos, 1)
        self.assertEqual(effects_sorted[0].prot_length, 599)
        self.assertEqual(effects_sorted[0].aa_change, None)

        self.assertEqual(effects_sorted[1].gene, "STIM2")
        self.assertEqual(effects_sorted[1].transcript_id, "NM_001169118_1")
        self.assertEqual(effects_sorted[1].strand, "+")
        self.assertEqual(effects_sorted[1].effect, "noStart")
        self.assertEqual(effects_sorted[1].prot_pos, 1)
        self.assertEqual(effects_sorted[1].prot_length, 754)
        self.assertEqual(effects_sorted[1].aa_change, None)

        self.assertEqual(effects_sorted[2].gene, "STIM2")
        self.assertEqual(effects_sorted[2].transcript_id, "NM_020860_1")
        self.assertEqual(effects_sorted[2].strand, "+")
        self.assertEqual(effects_sorted[2].effect, "noStart")
        self.assertEqual(effects_sorted[2].prot_pos, 1)
        self.assertEqual(effects_sorted[2].prot_length, 746)
        self.assertEqual(effects_sorted[2].aa_change, None)

    def test_chr5_68578558_ins_var(self):
        [effect] = VariantAnnotation.annotate_variant(self.gmDB, self.GA,
                                                      loc="5:68578558",
                                                      var="ins(TA)")

        self.assertEqual(effect.gene, "CCDC125")
        self.assertEqual(effect.transcript_id, "NM_176816_1")
        self.assertEqual(effect.strand, "-")
        self.assertEqual(effect.effect, "noEnd")
        self.assertEqual(effect.prot_pos, 512)
        self.assertEqual(effect.prot_length, 511)
        self.assertEqual(effect.aa_change, None)

    def test_chr6_33054014_ins_var(self):
        [effect] = VariantAnnotation.annotate_variant(self.gmDB, self.GA,
                                                      loc="6:33054014",
                                                      var="ins(C)")

        self.assertEqual(effect.gene, "HLA-DPB1")
        self.assertEqual(effect.transcript_id, "NM_002121_6")
        self.assertEqual(effect.strand, "+")
        self.assertEqual(effect.effect, "noEnd")
        self.assertEqual(effect.prot_pos, 259)
        self.assertEqual(effect.prot_length, 258)
        self.assertEqual(effect.aa_change, None)

    def test_chr1_152648485_del_var(self):
        [effect] = VariantAnnotation.annotate_variant(self.gmDB, self.GA,
                                                      loc="1:152648485",
                                                      var="del(13)")

        self.assertEqual(effect.gene, "LCE2C")
        self.assertEqual(effect.transcript_id, "NM_178429_1")
        self.assertEqual(effect.strand, "+")
        self.assertEqual(effect.effect, "noStart")
        self.assertEqual(effect.prot_pos, 1)
        self.assertEqual(effect.prot_length, 110)
        self.assertEqual(effect.aa_change, None)

    def test_chr1_7844919_del_var(self):
        [effect] = VariantAnnotation.annotate_variant(self.gmDB, self.GA,
                                                      loc="1:7844919",
                                                      var="del(21)")

        self.assertEqual(effect.gene, "PER3")
        self.assertEqual(effect.transcript_id, "NM_016831_1")
        self.assertEqual(effect.strand, "+")
        self.assertEqual(effect.effect, "noStart")
        self.assertEqual(effect.prot_pos, 1)
        self.assertEqual(effect.prot_length, 1201)
        self.assertEqual(effect.aa_change, None)


if __name__ == "__main__":
    unittest.main()
