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
    def test_chr20_5295014_ins_var(self):
        [effect] = VariantAnnotation.annotate_variant(self.gmDB, self.GA,
                                                      loc="20:5295014",
                                                      var="ins(AAG)")

        self.assertEqual(effect.gene, "PROKR2")
        self.assertEqual(effect.transcript_id, "NM_144773_1")
        self.assertEqual(effect.strand, "-")
        self.assertEqual(effect.effect, "noStart")
        self.assertEqual(effect.prot_pos, 1)
        self.assertEqual(effect.prot_length, 385)
        self.assertEqual(effect.aa_change, None)

    def test_chr1_33476432_ins_var(self):
        var = "ins(AGGATGTGGCTTTGGAGA)"
        effects = VariantAnnotation.annotate_variant(self.gmDB, self.GA,
                                                     loc="1:33476432", var=var)
        self.assertEqual(len(effects), 3)
        effects_sorted = sorted(effects, key=lambda k: k.transcript_id)

        self.assertEqual(effects_sorted[0].gene, "AK2")
        self.assertEqual(effects_sorted[0].transcript_id, "NM_001199199_1")
        self.assertEqual(effects_sorted[0].strand, "-")
        self.assertEqual(effects_sorted[0].effect, "no-frame-shift")
        self.assertEqual(effects_sorted[0].prot_pos, 225)
        self.assertEqual(effects_sorted[0].prot_length, 224)
        self.assertEqual(effects_sorted[0].aa_change, None)

        self.assertEqual(effects_sorted[1].gene, "AK2")
        self.assertEqual(effects_sorted[1].transcript_id, "NM_013411_1")
        self.assertEqual(effects_sorted[1].strand, "-")
        self.assertEqual(effects_sorted[1].effect, "no-frame-shift")
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

    def test_chr1_26158517_ins_var(self):
        [effect] = VariantAnnotation.annotate_variant(self.gmDB, self.GA,
                                                      loc="1:26158517",
                                                      var="ins(ACA)")

        self.assertEqual(effect.gene, "MTFR1L")
        self.assertEqual(effect.transcript_id, "NM_001099627_1")
        self.assertEqual(effect.strand, "+")
        self.assertEqual(effect.effect, "3'UTR")
        self.assertEqual(effect.prot_pos, None)
        self.assertEqual(effect.prot_length, None)
        self.assertEqual(effect.aa_change, None)

    def test_chr1_248903150_ins_var(self):
        var = "ins(AGTCTAGGCAATCTTCCCAGAATGGAAACCCAATCCACTCTTACTA)"
        [effect] = VariantAnnotation.annotate_variant(self.gmDB, self.GA,
                                                      loc="1:248903150",
                                                      var=var)

        self.assertEqual(effect.gene, "LYPD8")
        self.assertEqual(effect.transcript_id, "NM_001085474_1")
        self.assertEqual(effect.strand, "-")
        self.assertEqual(effect.effect, "frame-shift")
        self.assertEqual(effect.prot_pos, 1)
        self.assertEqual(effect.prot_length, 79)
        self.assertEqual(effect.aa_change, None)

    def test_chr1_20440608_ins_var(self):
        [effect] = VariantAnnotation.annotate_variant(self.gmDB, self.GA,
                                                      loc="1:20440608",
                                                      var="ins(T)")

        self.assertEqual(effect.gene, "PLA2G2D")
        self.assertEqual(effect.transcript_id, "NM_001271814_1")
        self.assertEqual(effect.strand, "-")
        self.assertEqual(effect.effect, "3'UTR")
        self.assertEqual(effect.prot_pos, None)
        self.assertEqual(effect.prot_length, None)
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
        self.assertEqual(effects_sorted[0].prot_pos, 3)
        self.assertEqual(effects_sorted[0].prot_length, 761)
        self.assertEqual(effects_sorted[0].aa_change, None)

        self.assertEqual(effects_sorted[1].gene, "SH2D2A")
        self.assertEqual(effects_sorted[1].transcript_id, "NM_001161441_1")
        self.assertEqual(effects_sorted[1].strand, "-")
        self.assertEqual(effects_sorted[1].effect, "intron")
        self.assertEqual(effects_sorted[1].prot_pos, 12)
        self.assertEqual(effects_sorted[1].prot_length, 400)
        self.assertEqual(effects_sorted[1].aa_change, None)

        self.assertEqual(effects_sorted[2].gene, "SH2D2A")
        self.assertEqual(effects_sorted[2].transcript_id, "NM_001161442_1")
        self.assertEqual(effects_sorted[2].strand, "-")
        self.assertEqual(effects_sorted[2].effect, "intron")
        self.assertEqual(effects_sorted[2].prot_pos, 4)
        self.assertEqual(effects_sorted[2].prot_length, 372)
        self.assertEqual(effects_sorted[2].aa_change, None)

        self.assertEqual(effects_sorted[3].gene, "SH2D2A")
        self.assertEqual(effects_sorted[3].transcript_id, "NM_001161444_1")
        self.assertEqual(effects_sorted[3].strand, "-")
        self.assertEqual(effects_sorted[3].effect, "intron")
        self.assertEqual(effects_sorted[3].prot_pos, 12)
        self.assertEqual(effects_sorted[3].prot_length, 390)
        self.assertEqual(effects_sorted[3].aa_change, None)

        self.assertEqual(effects_sorted[4].gene, "SH2D2A")
        self.assertEqual(effects_sorted[4].transcript_id, "NM_003975_1")
        self.assertEqual(effects_sorted[4].strand, "-")
        self.assertEqual(effects_sorted[4].effect, "intron")
        self.assertEqual(effects_sorted[4].prot_pos, 12)
        self.assertEqual(effects_sorted[4].prot_length, 390)
        self.assertEqual(effects_sorted[4].aa_change, None)

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
        self.assertEqual(effect.aa_change, None)

    def test_chr1_11740658_ins_var(self):
        [effect] = VariantAnnotation.annotate_variant(self.gmDB, self.GA,
                                                      loc="1:11740658",
                                                      var="ins(TCCT)")

        self.assertEqual(effect.gene, None)
        self.assertEqual(effect.transcript_id, None)
        self.assertEqual(effect.strand, None)
        self.assertEqual(effect.effect, "intergenic")
        self.assertEqual(effect.prot_pos, None)
        self.assertEqual(effect.prot_length, None)
        self.assertEqual(effect.aa_change, None)

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
        self.assertEqual(effects_sorted[0].prot_pos, 374)
        self.assertEqual(effects_sorted[0].prot_length, 389)
        self.assertEqual(effects_sorted[0].aa_change, None)

        self.assertEqual(effects_sorted[1].gene, "SKA3")
        self.assertEqual(effects_sorted[1].transcript_id, "NM_145061_1")
        self.assertEqual(effects_sorted[1].strand, "-")
        self.assertEqual(effects_sorted[1].effect, "frame-shift")
        self.assertEqual(effects_sorted[1].prot_pos, 414)
        self.assertEqual(effects_sorted[1].prot_length, 412)
        self.assertEqual(effects_sorted[1].aa_change, None)

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
        self.assertEqual(effects_sorted[0].prot_pos, 374)
        self.assertEqual(effects_sorted[0].prot_length, 389)
        self.assertEqual(effects_sorted[0].aa_change, None)

        self.assertEqual(effects_sorted[1].gene, "SKA3")
        self.assertEqual(effects_sorted[1].transcript_id, "NM_145061_1")
        self.assertEqual(effects_sorted[1].strand, "-")
        self.assertEqual(effects_sorted[1].effect, "no-frame-shift")
        self.assertEqual(effects_sorted[1].prot_pos, 414)
        self.assertEqual(effects_sorted[1].prot_length, 412)
        self.assertEqual(effects_sorted[1].aa_change, None)

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
        self.assertEqual(effects_sorted[0].prot_pos, 350)
        self.assertEqual(effects_sorted[0].prot_length, 2087)
        self.assertEqual(effects_sorted[0].aa_change, None)

        self.assertEqual(effects_sorted[1].gene, "ARHGAP32")
        self.assertEqual(effects_sorted[1].transcript_id, "NM_014715_1")
        self.assertEqual(effects_sorted[1].strand, "-")
        self.assertEqual(effects_sorted[1].effect, "noStart")
        self.assertEqual(effects_sorted[1].prot_pos, 1)
        self.assertEqual(effects_sorted[1].prot_length, 1739)
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


if __name__ == "__main__":
    unittest.main()
