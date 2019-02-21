from __future__ import unicode_literals
import unittest
import pytest
from variant_annotation.annotator import Variant
from .mocks import ExonMock
from .mocks import TranscriptModelMock
from .mocks import ReferenceGenomeMock
from .mocks import AnnotatorMock
from variant_annotation.effect_checkers.frame_shift \
    import FrameShiftEffectChecker
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
    request.cls.effect_checker = FrameShiftEffectChecker()


@pytest.mark.usefixtures("positive_strand")
class FrameShiftPositiveStrandTest(unittest.TestCase):
    def test_deletion_before_start(self):
        variant = Variant(loc="1:64", ref="A", alt="")
        request = AnnotationRequestFactory.create_annotation_request(
            self.annotator, variant, self.tm
        )
        effect = self.effect_checker.get_effect(request)
        self.assertEqual(effect, None)

    def test_insertion_before_start(self):
        variant = Variant(loc="1:64", ref="", alt="A")
        request = AnnotationRequestFactory.create_annotation_request(
            self.annotator, variant, self.tm
        )
        effect = self.effect_checker.get_effect(request)
        self.assertEqual(effect, None)

    def test_insertion_at_start_codon(self):
        variant = Variant(loc="1:65", ref="", alt="A")
        request = AnnotationRequestFactory.create_annotation_request(
            self.annotator, variant, self.tm
        )
        effect = self.effect_checker.get_effect(request)
        self.assertEqual(effect.effect, "frame-shift")

    def test_insertion_after_start_codon(self):
        variant = Variant(loc="1:66", ref="", alt="ABC")
        request = AnnotationRequestFactory.create_annotation_request(
            self.annotator, variant, self.tm
        )
        effect = self.effect_checker.get_effect(request)
        self.assertEqual(effect.effect, "no-frame-shift")

    def test_insertion_at_start_codon_2(self):
        variant = Variant(loc="1:65", ref="", alt="BC")
        request = AnnotationRequestFactory.create_annotation_request(
            self.annotator, variant, self.tm
        )
        effect = self.effect_checker.get_effect(request)
        self.assertEqual(effect.effect, "frame-shift")

    def test_deletion_start_codon(self):
        variant = Variant(loc="1:65", ref="ABC", alt="")
        request = AnnotationRequestFactory.create_annotation_request(
            self.annotator, variant, self.tm
        )
        effect = self.effect_checker.get_effect(request)
        self.assertEqual(effect.effect, "no-frame-shift")
