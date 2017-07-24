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

    def test_chr1_120387132_del_var(self):
        [effect] = VariantAnnotation.annotate_variant(self.gmDB, self.GA,
                                                      loc="1:120387132",
                                                      var="del(71)")

        self.assertEqual(effect.gene, "NBPF7")
        self.assertEqual(effect.transcript_id, "NM_001047980_1")
        self.assertEqual(effect.strand, "-")
        self.assertEqual(effect.effect, "noStart")
        # self.assertEqual(effect.prot_pos, 1)
        # self.assertEqual(effect.prot_length, 422)
        self.assertEqual(effect.aa_change, None)

    def test_chr1_16890438_del_var(self):
        [effect] = VariantAnnotation.annotate_variant(self.gmDB, self.GA,
                                                      loc="1:16890438",
                                                      var="del(1)")

        self.assertEqual(effect.gene, "NBPF1")
        self.assertEqual(effect.transcript_id, "NM_017940_1")
        self.assertEqual(effect.strand, "-")
        self.assertEqual(effect.effect, "no-frame-shift")
        # self.assertEqual(effect.prot_pos, 1142)
        # self.assertEqual(effect.prot_length, 1141)
        self.assertEqual(effect.aa_change, None)

    def test_chr1_20440608_ins_var(self):
        [effect] = VariantAnnotation.annotate_variant(self.gmDB, self.GA,
                                                      loc="1:20440608",
                                                      var="ins(T)")

        self.assertEqual(effect.gene, "PLA2G2D")
        self.assertEqual(effect.transcript_id, "NM_001271814_1")
        self.assertEqual(effect.strand, "-")
        self.assertEqual(effect.effect, "3'UTR")
        # self.assertEqual(effect.prot_pos, None)
        # self.assertEqual(effect.prot_length, None)
        self.assertEqual(effect.aa_change, None)

    def test_chr1_26142208_ins_var(self):
        [effect] = VariantAnnotation.annotate_variant(self.gmDB, self.GA,
                                                      loc="1:26142208",
                                                      var="ins(AG)")

        self.assertEqual(effect.gene, None)
        self.assertEqual(effect.transcript_id, None)
        self.assertEqual(effect.strand, None)
        self.assertEqual(effect.effect, "intergenic")
        # self.assertEqual(effect.prot_pos, None)
        # self.assertEqual(effect.prot_length, None)
        self.assertEqual(effect.aa_change, None)

    def test_chr1_26158517_ins_var(self):
        [effect] = VariantAnnotation.annotate_variant(self.gmDB, self.GA,
                                                      loc="1:26158517",
                                                      var="ins(ACA)")

        self.assertEqual(effect.gene, "MTFR1L")
        self.assertEqual(effect.transcript_id, "NM_001099627_1")
        self.assertEqual(effect.strand, "+")
        self.assertEqual(effect.effect, "3'UTR")
        # self.assertEqual(effect.prot_pos, None)
        # self.assertEqual(effect.prot_length, None)
        self.assertEqual(effect.aa_change, None)

    def test_chr1_31845860_ins_var(self):
        [effect] = VariantAnnotation.annotate_variant(self.gmDB, self.GA,
                                                      loc="1:31845860",
                                                      var="ins(ATAG)")

        self.assertEqual(effect.gene, None)
        self.assertEqual(effect.transcript_id, None)
        self.assertEqual(effect.strand, None)
        self.assertEqual(effect.effect, "intergenic")
        # self.assertEqual(effect.prot_pos, None)
        # self.assertEqual(effect.prot_length, None)
        self.assertEqual(effect.aa_change, None)

    def test_chr1_44686290_ins_var(self):
        [effect] = VariantAnnotation.annotate_variant(self.gmDB, self.GA,
                                                      loc="1:44686290",
                                                      var="ins(A)")

        self.assertEqual(effect.gene, None)
        self.assertEqual(effect.transcript_id, None)
        self.assertEqual(effect.strand, None)
        self.assertEqual(effect.effect, "intergenic")
        # self.assertEqual(effect.prot_pos, None)
        # self.assertEqual(effect.prot_length, None)
        self.assertEqual(effect.aa_change, None)

    def test_chr1_45446840_ins_var(self):
        [effect] = VariantAnnotation.annotate_variant(self.gmDB, self.GA,
                                                      loc="1:45446840",
                                                      var="ins(T)")

        self.assertEqual(effect.gene, None)
        self.assertEqual(effect.transcript_id, None)
        self.assertEqual(effect.strand, None)
        self.assertEqual(effect.effect, "intergenic")
        # self.assertEqual(effect.prot_pos, None)
        # self.assertEqual(effect.prot_length, None)
        self.assertEqual(effect.aa_change, None)

    def test_first_codon_ins_var(self):
        [effect] = VariantAnnotation.annotate_variant(self.gmDB, self.GA,
                                                      loc="1:3527831",
                                                      var="ins(A)")
        self.assertEqual(effect.gene, "MEGF6")
        self.assertEqual(effect.transcript_id, "NM_001409_1")
        self.assertEqual(effect.strand, "-")
        self.assertEqual(effect.effect, "frame-shift")
        # self.assertEqual(effect.prot_pos, 1)
        # self.assertEqual(effect.prot_length, 1541)
        self.assertEqual(effect.aa_change, None)

    def test_first_codon_ins_integenic_var(self):
        [effect] = VariantAnnotation.annotate_variant(self.gmDB, self.GA,
                                                      loc="1:3407092",
                                                      var="ins(A)")
        self.assertEqual(effect.gene, None)
        self.assertEqual(effect.transcript_id, None)
        self.assertEqual(effect.strand, None)
        self.assertEqual(effect.effect, "intergenic")
        # self.assertEqual(effect.prot_pos, None)
        # self.assertEqual(effect.prot_length, None)
        self.assertEqual(effect.aa_change, None)

    def test_chr9_139839774_ins_var(self):
        var = "ins(TGCTGCCGCCACCA)"
        [effect] = VariantAnnotation.annotate_variant(self.gmDB, self.GA,
                                                      loc="9:139839774",
                                                      var=var)

        self.assertEqual(effect.gene, None)
        self.assertEqual(effect.transcript_id, None)
        self.assertEqual(effect.strand, None)
        self.assertEqual(effect.effect, "intergenic")
        # self.assertEqual(effect.prot_pos, None)
        # self.assertEqual(effect.prot_length, None)
        self.assertEqual(effect.aa_change, None)

    # Why only one effect???
    def test_chr7_149461804_del_var(self):
        [effect] = VariantAnnotation.annotate_variant(self.gmDB, self.GA,
                                                      loc="7:149461804",
                                                      var="del(1)")

        self.assertEqual(effect.gene, "ZNF467")
        self.assertEqual(effect.transcript_id, "NM_207336_1")
        self.assertEqual(effect.strand, "-")
        self.assertEqual(effect.effect, "no-frame-shift")
        # self.assertEqual(effect.prot_pos, 596)
        # self.assertEqual(effect.prot_length, 595)
        self.assertEqual(effect.aa_change, None)

    def test_chr6_161557574_ins_var(self):
        [effect] = VariantAnnotation.annotate_variant(self.gmDB, self.GA,
                                                      loc="6:161557574",
                                                      var="ins(AGTC)")

        self.assertEqual(effect.gene, None)
        self.assertEqual(effect.transcript_id, None)
        self.assertEqual(effect.strand, None)
        self.assertEqual(effect.effect, "intergenic")
        # self.assertEqual(effect.prot_pos, None)
        # self.assertEqual(effect.prot_length, None)
        self.assertEqual(effect.aa_change, None)

    # Why only two effects???
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

    def test_chr1_92546129_ins_var(self):
        [effect] = VariantAnnotation.annotate_variant(self.gmDB, self.GA,
                                                      loc="1:92546129",
                                                      var="ins(A)")

        self.assertEqual(effect.gene, None)
        self.assertEqual(effect.transcript_id, None)
        self.assertEqual(effect.strand, None)
        self.assertEqual(effect.effect, "intergenic")
        # self.assertEqual(effect.prot_pos, None)
        # self.assertEqual(effect.prot_length, None)
        self.assertEqual(effect.aa_change, None)

    # Why only one?
    def test_chr4_100544005_ins_var(self):
        [effect] = VariantAnnotation.annotate_variant(self.gmDB, self.GA,
                                                      loc="4:100544005",
                                                      var="ins(GAAA)")

        self.assertEqual(effect.gene, "MTTP")
        self.assertEqual(effect.transcript_id, "NM_000253_1")
        self.assertEqual(effect.strand, "+")
        self.assertEqual(effect.effect, "frame-shift")
        # self.assertEqual(effect.prot_pos, 895)
        # self.assertEqual(effect.prot_length, 894)
        self.assertEqual(effect.aa_change, None)

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
        self.assertEqual(effects_sorted[1].effect, "frame-shift")
        # self.assertEqual(effects_sorted[1].prot_pos, 1)
        # self.assertEqual(effects_sorted[1].prot_length, 843)
        self.assertEqual(effects_sorted[1].aa_change, None)

    def test_chr2_237172988_ins_var(self):
        [effect] = VariantAnnotation.annotate_variant(self.gmDB, self.GA,
                                                      loc="2:237172988",
                                                      var="ins(TTGTTACG)")

        self.assertEqual(effect.gene, "ASB18")
        self.assertEqual(effect.transcript_id, "NM_212556_1")
        self.assertEqual(effect.strand, "-")
        self.assertEqual(effect.effect, "5'UTR")
        # self.assertEqual(effect.prot_pos, None)
        # self.assertEqual(effect.prot_length, None)
        self.assertEqual(effect.aa_change, None)

    def test_chr1_20490475_del_var(self):
        [effect] = VariantAnnotation.annotate_variant(self.gmDB, self.GA,
                                                      loc="1:20490475",
                                                      var="del(18)")

        self.assertEqual(effect.gene, "PLA2G2C")
        self.assertEqual(effect.transcript_id, "NM_001105572_1")
        self.assertEqual(effect.strand, "-")
        self.assertEqual(effect.effect, "noEnd")
        # self.assertEqual(effect.prot_pos, 151)
        # self.assertEqual(effect.prot_length, 151)
        self.assertEqual(effect.aa_change, None)

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
        # self.assertEqual(effects_sorted[0].prot_pos, 248)
        # self.assertEqual(effects_sorted[0].prot_length, 262)
        self.assertEqual(effects_sorted[0].aa_change, None)

        self.assertEqual(effects_sorted[1].gene, "NEURL2")
        self.assertEqual(effects_sorted[1].transcript_id, "NM_080749_1")
        self.assertEqual(effects_sorted[1].strand, "-")
        self.assertEqual(effects_sorted[1].effect, "splice-site")
        # self.assertEqual(effects_sorted[1].prot_pos, 248)
        # self.assertEqual(effects_sorted[1].prot_length, 286)
        self.assertEqual(effects_sorted[1].aa_change, None)

    def test_chr13_45911524_ins_var(self):
        var = "ins(ACATTTTTCCATTTCTAAACCAT)"
        [effect] = VariantAnnotation.annotate_variant(self.gmDB, self.GA,
                                                      loc="13:45911524",
                                                      var=var)

        self.assertEqual(effect.gene, "TPT1")
        self.assertEqual(effect.transcript_id, "NM_003295_1")
        self.assertEqual(effect.strand, "-")
        self.assertEqual(effect.effect, "splice-site")
        # self.assertEqual(effect.prot_pos, 173)
        # self.assertEqual(effect.prot_length, 173)
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
        self.assertEqual(effects_sorted[0].effect, "splice-site")
        # self.assertEqual(effects_sorted[0].prot_pos, 949)
        # self.assertEqual(effects_sorted[0].prot_length, 1176)
        self.assertEqual(effects_sorted[0].aa_change, None)

        self.assertEqual(effects_sorted[1].gene, "ATP13A2")
        self.assertEqual(effects_sorted[1].transcript_id, "NM_001141974_1")
        self.assertEqual(effects_sorted[1].strand, "-")
        self.assertEqual(effects_sorted[1].effect, "splice-site")
        # self.assertEqual(effects_sorted[1].prot_pos, 910)
        # self.assertEqual(effects_sorted[1].prot_length, 1159)
        self.assertEqual(effects_sorted[1].aa_change, None)

        self.assertEqual(effects_sorted[2].gene, "ATP13A2")
        self.assertEqual(effects_sorted[2].transcript_id, "NM_022089_1")
        self.assertEqual(effects_sorted[2].strand, "-")
        self.assertEqual(effects_sorted[2].effect, "splice-site")
        # self.assertEqual(effects_sorted[2].prot_pos, 954)
        # self.assertEqual(effects_sorted[2].prot_length, 1181)
        self.assertEqual(effects_sorted[2].aa_change, None)

    def test_chr13_21729290_ins_var(self):
        var = "ins(CAGTTTTCTTTGTTGCTGACATCTCGGATGTTCTGTCCATGTTTAAGGAACCTTTTA)"
        effects = VariantAnnotation.annotate_variant(self.gmDB, self.GA,
                                                     loc="13:21729290",
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
        self.assertEqual(effects_sorted[1].effect, "no-frame-shift")
        # self.assertEqual(effects_sorted[1].prot_pos, 414)
        # self.assertEqual(effects_sorted[1].prot_length, 412)
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
        # self.assertEqual(effects_sorted[0].prot_pos, None)
        # self.assertEqual(effects_sorted[0].prot_length, None)
        self.assertEqual(effects_sorted[0].aa_change, None)

        self.assertEqual(effects_sorted[1].gene, "LOC100130417")
        self.assertEqual(effects_sorted[1].transcript_id, "NR_026874_1")
        self.assertEqual(effects_sorted[1].strand, "-")
        self.assertEqual(effects_sorted[1].effect, "unknown")
        # self.assertEqual(effects_sorted[1].prot_pos, None)
        # self.assertEqual(effects_sorted[1].prot_length, None)
        self.assertEqual(effects_sorted[1].aa_change, None)

        self.assertEqual(effects_sorted[2].gene, "FAM41C")
        self.assertEqual(effects_sorted[2].transcript_id, "NR_027055_1")
        self.assertEqual(effects_sorted[2].strand, "-")
        self.assertEqual(effects_sorted[2].effect, "unknown")
        # self.assertEqual(effects_sorted[2].prot_pos, None)
        # self.assertEqual(effects_sorted[2].prot_length, None)
        self.assertEqual(effects_sorted[2].aa_change, None)


if __name__ == "__main__":
    unittest.main()
