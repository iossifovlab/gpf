import unittest
from variant_annotation.mutation import GenomicSequence
from variant_annotation.annotator import Variant


class ExonMock:
    def __init__(self, start, stop, frame):
        self.start = start
        self.stop = stop
        self.frame = frame


class TranscriptModelMock:
    def __init__(self, strand, cds_start, cds_end, exons):
        self.strand = strand
        self.cds = [cds_start, cds_end]
        self.exons = exons
        self.chr = "1"


class ReferenceGenomeMock:
    def getSequence(self, chromosome, pos, pos_last):
        print("get", chromosome, pos, pos_last)
        return "".join([chr(i) for i in range(pos, pos_last + 1)])


class AnnotatorMock:
    def __init__(self, reference_genome):
        self.reference_genome = reference_genome


class GenomicSequenceTest(unittest.TestCase):
    def test_get_coding_left_inner(self):
        annotator = AnnotatorMock(ReferenceGenomeMock())
        exons = [ExonMock(50, 100, 0), ExonMock(400, 500, 2)]
        tm = TranscriptModelMock("+", 1, 2000, exons)
        gen_seq = GenomicSequence(annotator, None, tm)
        self.assertEqual(gen_seq.get_coding_left(98, 2, 0), "ab")

    def test_get_coding_left_cross_border(self):
        annotator = AnnotatorMock(ReferenceGenomeMock())
        exons = [ExonMock(50, 100, 0), ExonMock(120, 500, 2)]
        tm = TranscriptModelMock("+", 1, 2000, exons)
        gen_seq = GenomicSequence(annotator, None, tm)
        self.assertEqual(gen_seq.get_coding_left(120, 2, 1), "dx")

    def test_get_coding_left_cross_multiple_borders(self):
        annotator = AnnotatorMock(ReferenceGenomeMock())
        exons = [ExonMock(i, i, 0) for i in range(97, 120, 2)]
        tm = TranscriptModelMock("+", 1, 2000, exons)
        gen_seq = GenomicSequence(annotator, None, tm)
        self.assertEqual(gen_seq.get_coding_left(119, 10, 11), "egikmoqsuw")

    def test_get_coding_right_inner(self):
        annotator = AnnotatorMock(ReferenceGenomeMock())
        exons = [ExonMock(50, 100, 0), ExonMock(400, 500, 2)]
        tm = TranscriptModelMock("+", 1, 2000, exons)
        gen_seq = GenomicSequence(annotator, None, tm)
        self.assertEqual(gen_seq.get_coding_right(97, 2, 0), "ab")

    def test_get_coding_right_cross_border(self):
        annotator = AnnotatorMock(ReferenceGenomeMock())
        exons = [ExonMock(50, 100, 0), ExonMock(120, 500, 2)]
        tm = TranscriptModelMock("+", 1, 2000, exons)
        gen_seq = GenomicSequence(annotator, None, tm)
        self.assertEqual(gen_seq.get_coding_right(100, 2, 0), "dx")

    def test_get_coding_right_cross_multiple_borders(self):
        annotator = AnnotatorMock(ReferenceGenomeMock())
        exons = [ExonMock(i, i, 0) for i in range(97, 120, 2)]
        tm = TranscriptModelMock("+", 1, 2000, exons)
        gen_seq = GenomicSequence(annotator, None, tm)
        self.assertEqual(gen_seq.get_coding_right(101, 10, 2), "egikmoqsuw")

    def test_get_coding_region_for_pos(self):
        annotator = AnnotatorMock(ReferenceGenomeMock())
        exons = [ExonMock(i, i, 0) for i in range(97, 120, 2)]
        tm = TranscriptModelMock("+", 1, 2000, exons)
        gen_seq = GenomicSequence(annotator, None, tm)
        self.assertEqual(gen_seq.get_coding_region_for_pos(119), 11)

    def test_invalid_get_coding_region_for_pos(self):
        annotator = AnnotatorMock(ReferenceGenomeMock())
        exons = [ExonMock(i, i, 0) for i in range(97, 120, 2)]
        tm = TranscriptModelMock("+", 1, 2000, exons)
        gen_seq = GenomicSequence(annotator, None, tm)
        self.assertEqual(gen_seq.get_coding_region_for_pos(130), None)

    def test_get_frame(self):
        annotator = AnnotatorMock(ReferenceGenomeMock())
        exons = [ExonMock(50, 100, 0),
                 ExonMock(200, 250, 1),
                 ExonMock(400, 500, 2)]
        tm = TranscriptModelMock("+", 1, 2000, exons)
        gen_seq = GenomicSequence(annotator, None, tm)
        self.assertEqual(gen_seq.get_frame(54, 0), 1)
        self.assertEqual(gen_seq.get_frame(56, 0), 0)

        self.assertEqual(gen_seq.get_frame(201, 1), 2)

        self.assertEqual(gen_seq.get_frame(401, 2), 0)

    def test_get_codons(self):
        variant = Variant(loc="1:80", ref="-" * 15, alt="A")
        annotator = AnnotatorMock(ReferenceGenomeMock())
        exons = [ExonMock(65, 70, 0),
                 ExonMock(80, 90, 1),
                 ExonMock(100, 110, 2)]
        tm = TranscriptModelMock("+", 1, 2000, exons)
        gen_seq = GenomicSequence(annotator, variant, tm)
        ref_codons, alt_codons = gen_seq.get_codons()
        self.assertEqual(ref_codons, "FPQRSTUVWXYZdefghi")
        self.assertEqual(alt_codons, "FAd")
