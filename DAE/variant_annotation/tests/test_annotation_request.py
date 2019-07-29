import unittest
import pytest
from variant_annotation.annotator import Variant
from .mocks import ExonMock
from .mocks import TranscriptModelMock
from .mocks import ReferenceGenomeMock
from .mocks import AnnotatorMock
from variant_annotation.annotation_request import AnnotationRequestFactory


@pytest.fixture(scope="class")
def positive_strand(request):
    request.cls.annotator = AnnotatorMock(ReferenceGenomeMock())
    exons = [ExonMock(60, 70, 0),
             ExonMock(80, 90, 1),
             ExonMock(100, 110, 2)]
    coding = [ExonMock(65, 70, 0),
              ExonMock(80, 90, 1),
              ExonMock(100, 110, 2)]
    request.cls.tm = TranscriptModelMock("+", 65, 2000, exons, coding)


@pytest.mark.usefixtures("positive_strand")
class AnnotationRequestPositiveStrandTest(unittest.TestCase):
    def test_exonic_distance(self):
        variant = Variant(loc="1:64", ref="A", alt="")
        request = AnnotationRequestFactory.create_annotation_request(
            self.annotator, variant, self.tm
        )
        self.assertEqual(request.get_exonic_distance(60, 61), 1)
        self.assertEqual(request.get_exonic_distance(60, 70), 10)
        self.assertEqual(request.get_exonic_distance(60, 80), 11)
        self.assertEqual(request.get_exonic_distance(70, 80), 1)

    def test_exonic_pos_first_exon(self):
        variant = Variant(loc="1:64", ref="A", alt="")
        request = AnnotationRequestFactory.create_annotation_request(
            self.annotator, variant, self.tm
        )
        self.assertEqual(request.get_exonic_position(), 5)
        self.assertEqual(request.get_exonic_length(), 33)

    def test_exonic_pos_last_in_first_exon(self):
        variant = Variant(loc="1:70", ref="A", alt="")
        request = AnnotationRequestFactory.create_annotation_request(
            self.annotator, variant, self.tm
        )
        self.assertEqual(request.get_exonic_position(), 11)
        self.assertEqual(request.get_exonic_length(), 33)

    def test_exonic_pos_second_exon(self):
        variant = Variant(loc="1:80", ref="A", alt="")
        request = AnnotationRequestFactory.create_annotation_request(
            self.annotator, variant, self.tm
        )
        self.assertEqual(request.get_exonic_position(), 12)
        self.assertEqual(request.get_exonic_length(), 33)

    def test_exonic_pos_last_exon(self):
        variant = Variant(loc="1:110", ref="A", alt="")
        request = AnnotationRequestFactory.create_annotation_request(
            self.annotator, variant, self.tm
        )
        self.assertEqual(request.get_exonic_position(), 33)
        self.assertEqual(request.get_exonic_length(), 33)
