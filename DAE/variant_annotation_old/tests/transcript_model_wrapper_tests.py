from __future__ import unicode_literals
from builtins import object
import unittest
from variant_annotation.mutation import TranscriptModelWrapper


class ExonMock(object):
    def __init__(self, start, stop, frame):
        self.start = start
        self.stop = stop
        self.frame = frame


class TranscriptModelMock(object):
    def __init__(self, strand, cds_start, cds_end, exons):
        self.strand = strand
        self.cds = [cds_start, cds_end]
        self.exons = exons


class TranscriptModelWrapperTest(unittest.TestCase):
    def test_pos_strand_zero_frame_offset_inside_cds(self):
        exons = [ExonMock(10, 200, 0), ExonMock(400, 500, 2)]
        tm = TranscriptModelMock("+", 1, 2000, exons)
        tmw = TranscriptModelWrapper(tm, None)
        self.assertEqual(tmw.get_codon_start_pos(20), 19)

    def test_pos_strand_one_frame_offset_inside_cds(self):
        exons = [ExonMock(10, 200, 1), ExonMock(400, 500, 2)]
        tm = TranscriptModelMock("+", 1, 2000, exons)
        tmw = TranscriptModelWrapper(tm, None)
        self.assertEqual(tmw.get_codon_start_pos(20), 18)

    def test_pos_strand_two_frame_offset_inside_cds(self):
        exons = [ExonMock(10, 200, 2), ExonMock(400, 500, 2)]
        tm = TranscriptModelMock("+", 1, 2000, exons)
        tmw = TranscriptModelWrapper(tm, None)
        self.assertEqual(tmw.get_codon_start_pos(20), 20)

    def test_neg_strand_zero_frame_offset_inside_cds(self):
        exons = [ExonMock(10, 200, 0), ExonMock(400, 500, 2)]
        tm = TranscriptModelMock("-", 1, 2000, exons)
        tmw = TranscriptModelWrapper(tm, None)
        self.assertEqual(tmw.get_codon_start_pos(190), 191)

    def test_neg_strand_one_frame_offset_inside_cds(self):
        exons = [ExonMock(10, 200, 1), ExonMock(400, 500, 2)]
        tm = TranscriptModelMock("-", 1, 2000, exons)
        tmw = TranscriptModelWrapper(tm, None)
        self.assertEqual(tmw.get_codon_start_pos(190), 192)

    def test_neg_strand_two_frame_offset_inside_cds(self):
        exons = [ExonMock(10, 200, 2), ExonMock(400, 500, 2)]
        tm = TranscriptModelMock("-", 1, 2000, exons)
        tmw = TranscriptModelWrapper(tm, None)
        self.assertEqual(tmw.get_codon_start_pos(190), 190)
