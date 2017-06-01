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


if __name__ == "__main__":
    unittest.main()
