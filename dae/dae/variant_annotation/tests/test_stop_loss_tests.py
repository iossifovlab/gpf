import unittest
import pytest
from dae.variant_annotation.annotator import Variant
from .mocks import ExonMock
from .mocks import TranscriptModelMock
from .mocks import ReferenceGenomeMock
from .mocks import AnnotatorMock
from dae.variant_annotation.effect_checkers.stop_loss \
    import StopLossEffectChecker
from dae.variant_annotation.annotation_request import AnnotationRequestFactory


@pytest.fixture(scope="class")
def positive_strand(request):
    request.cls.annotator = AnnotatorMock(ReferenceGenomeMock())
    exons = [ExonMock(60, 70, 0),
             ExonMock(80, 90, 1),
             ExonMock(100, 110, 2)]
    coding = [ExonMock(65, 70, 0),
              ExonMock(80, 90, 1),
              ExonMock(100, 110, 2)]
    request.cls.tm = TranscriptModelMock("+", 65, 110, exons, coding)
    request.cls.effect_checker = StopLossEffectChecker()


@pytest.fixture(scope="class")
def negative_strand(request):
    request.cls.annotator = AnnotatorMock(ReferenceGenomeMock())
    exons = [ExonMock(60, 70, 0),
             ExonMock(80, 90, 1),
             ExonMock(100, 110, 2)]
    coding = [ExonMock(65, 70, 0),
              ExonMock(80, 90, 1),
              ExonMock(100, 110, 2)]
    request.cls.tm = TranscriptModelMock("-", 65, 110, exons, coding)
    request.cls.effect_checker = StopLossEffectChecker()


@pytest.mark.usefixtures("positive_strand")
class StopLossPositiveStrandTest(unittest.TestCase):
    def test_deletion_before_end(self):
        variant = Variant(loc="1:105", ref="ABC", alt="")
        request = AnnotationRequestFactory.create_annotation_request(
            self.annotator, variant, self.tm
        )
        effect = self.effect_checker.get_effect(request)
        self.assertEqual(effect, None)

    def test_deletion_at_end(self):
        variant = Variant(loc="1:109", ref="ABC", alt="")
        request = AnnotationRequestFactory.create_annotation_request(
            self.annotator, variant, self.tm
        )
        effect = self.effect_checker.get_effect(request)
        self.assertEqual(effect.effect, "noEnd")

    def test_deletion_after_end(self):
        variant = Variant(loc="1:111", ref="ABC", alt="")
        request = AnnotationRequestFactory.create_annotation_request(
            self.annotator, variant, self.tm
        )
        effect = self.effect_checker.get_effect(request)
        self.assertEqual(effect, None)

    def test_insertion_before_end(self):
        variant = Variant(loc="1:107", ref="", alt="ABC")
        request = AnnotationRequestFactory.create_annotation_request(
            self.annotator, variant, self.tm
        )
        effect = self.effect_checker.get_effect(request)
        self.assertEqual(effect, None)

    def test_insertion_at_end(self):
        variant = Variant(loc="1:108", ref="", alt="ABC")
        request = AnnotationRequestFactory.create_annotation_request(
            self.annotator, variant, self.tm
        )
        effect = self.effect_checker.get_effect(request)
        self.assertEqual(effect.effect, "noEnd")

    def test_insertion_after_end(self):
        variant = Variant(loc="1:111", ref="", alt="ABC")
        request = AnnotationRequestFactory.create_annotation_request(
            self.annotator, variant, self.tm
        )
        effect = self.effect_checker.get_effect(request)
        self.assertEqual(effect, None)


@pytest.mark.usefixtures("negative_strand")
class StopLossNegativeStrandTest(unittest.TestCase):
    def test_deletion_before_end(self):
        variant = Variant(loc="1:62", ref="ABC", alt="")
        request = AnnotationRequestFactory.create_annotation_request(
            self.annotator, variant, self.tm
        )
        effect = self.effect_checker.get_effect(request)
        self.assertEqual(effect, None)

    def test_deletion_at_end(self):
        variant = Variant(loc="1:63", ref="ABC", alt="")
        request = AnnotationRequestFactory.create_annotation_request(
            self.annotator, variant, self.tm
        )
        effect = self.effect_checker.get_effect(request)
        self.assertEqual(effect.effect, "noEnd")

    def test_deletion_after_end(self):
        variant = Variant(loc="1:68", ref="ABC", alt="")
        request = AnnotationRequestFactory.create_annotation_request(
            self.annotator, variant, self.tm
        )
        effect = self.effect_checker.get_effect(request)
        self.assertEqual(effect, None)

    def test_insertion_before_end(self):
        variant = Variant(loc="1:64", ref="", alt="ABC")
        request = AnnotationRequestFactory.create_annotation_request(
            self.annotator, variant, self.tm
        )
        effect = self.effect_checker.get_effect(request)
        self.assertEqual(effect, None)

    def test_insertion_at_end(self):
        variant = Variant(loc="1:65", ref="", alt="ABC")
        request = AnnotationRequestFactory.create_annotation_request(
            self.annotator, variant, self.tm
        )
        effect = self.effect_checker.get_effect(request)
        self.assertEqual(effect.effect, "noEnd")

    def test_insertion_after_end(self):
        variant = Variant(loc="1:68", ref="", alt="ABC")
        request = AnnotationRequestFactory.create_annotation_request(
            self.annotator, variant, self.tm
        )
        effect = self.effect_checker.get_effect(request)
        self.assertEqual(effect, None)
