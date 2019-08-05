import unittest
import pytest
from dae.variant_annotation.annotator import Variant
from .mocks import ExonMock
from .mocks import TranscriptModelMock
from .mocks import ReferenceGenomeMock
from .mocks import AnnotatorMock
from dae.variant_annotation.effect_checkers.utr \
    import UTREffectChecker
from dae.variant_annotation.annotation_request import AnnotationRequestFactory


@pytest.fixture(scope="class")
def positive_strand(request):
    request.cls.annotator = AnnotatorMock(ReferenceGenomeMock())
    exons = [ExonMock(60, 70, 0),
             ExonMock(80, 90, 1),
             ExonMock(100, 110, 2),
             ExonMock(150, 170, 2)]
    coding = [ExonMock(85, 90, 1),
              ExonMock(100, 105, 2)]
    request.cls.tm = TranscriptModelMock("+", 85, 105, exons, coding)
    request.cls.effect_checker = UTREffectChecker()


@pytest.mark.usefixtures("positive_strand")
class UTRPositiveStrandTest(unittest.TestCase):
    def test_deletion_before_start(self):
        variant = Variant(loc="1:65", ref="A", alt="")
        request = AnnotationRequestFactory.create_annotation_request(
            self.annotator, variant, self.tm
        )
        effect = self.effect_checker.get_effect(request)
        self.assertEqual(effect.effect, "5'UTR")
        self.assertEqual(effect.dist_from_coding, 11)

    def test_deletion_after_end_same_exon(self):
        variant = Variant(loc="1:108", ref="A", alt="")
        request = AnnotationRequestFactory.create_annotation_request(
            self.annotator, variant, self.tm
        )
        effect = self.effect_checker.get_effect(request)
        self.assertEqual(effect.effect, "3'UTR")
        self.assertEqual(effect.dist_from_coding, 3)

    def test_deletion_after_end_same_exon_end(self):
        variant = Variant(loc="1:110", ref="A", alt="")
        request = AnnotationRequestFactory.create_annotation_request(
            self.annotator, variant, self.tm
        )
        effect = self.effect_checker.get_effect(request)
        self.assertEqual(effect.effect, "3'UTR")
        self.assertEqual(effect.dist_from_coding, 5)

    def test_deletion_after_end_last_exon(self):
        variant = Variant(loc="1:151", ref="A", alt="")
        request = AnnotationRequestFactory.create_annotation_request(
            self.annotator, variant, self.tm
        )
        effect = self.effect_checker.get_effect(request)
        self.assertEqual(effect.effect, "3'UTR")
        self.assertEqual(effect.dist_from_coding, 7)
