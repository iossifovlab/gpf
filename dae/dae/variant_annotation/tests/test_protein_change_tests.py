import unittest
import pytest
from dae.variant_annotation.annotator import Variant
from .mocks import ExonMock
from .mocks import TranscriptModelMock
from .mocks import ReferenceGenomeMock
from .mocks import AnnotatorMock
from dae.variant_annotation.effect_checkers.protein_change \
    import ProteinChangeEffectChecker
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
    request.cls.effect_checker = ProteinChangeEffectChecker()


@pytest.mark.usefixtures("positive_strand")
class ProteinChangePositiveStrandTest(unittest.TestCase):
    def test_missense(self):
        variant = Variant(loc="1:66", ref="ABC", alt="DEF")
        request = AnnotationRequestFactory.create_annotation_request(
            self.annotator, variant, self.tm
        )
        request.cod2aa = lambda codon: codon
        effect = self.effect_checker.get_effect(request)
        self.assertEqual(effect.effect, "missense")

    def test_nonsense(self):
        variant = Variant(loc="1:65", ref="ABC", alt="End")
        request = AnnotationRequestFactory.create_annotation_request(
            self.annotator, variant, self.tm
        )
        request.cod2aa = lambda codon: codon
        effect = self.effect_checker.get_effect(request)
        self.assertEqual(effect.effect, "nonsense")

    def test_synonymous(self):
        variant = Variant(loc="1:65", ref="ABC", alt="End")
        request = AnnotationRequestFactory.create_annotation_request(
            self.annotator, variant, self.tm
        )
        request.cod2aa = lambda codon: "Asn"
        effect = self.effect_checker.get_effect(request)
        self.assertEqual(effect.effect, "synonymous")

    def test_multiple_codons_missense(self):
        variant = Variant(loc="1:66", ref="ABCDEF", alt="abcdef")
        request = AnnotationRequestFactory.create_annotation_request(
            self.annotator, variant, self.tm
        )
        request.cod2aa = lambda codon: codon
        effect = self.effect_checker.get_effect(request)
        self.assertEqual(effect.effect, "missense")

    def test_multiple_codons_nonsense(self):
        variant = Variant(loc="1:65", ref="ABCDEF", alt="EndPBC")
        request = AnnotationRequestFactory.create_annotation_request(
            self.annotator, variant, self.tm
        )
        request.cod2aa = lambda codon: codon
        effect = self.effect_checker.get_effect(request)
        self.assertEqual(effect.effect, "nonsense")

    def test_multiple_codons_synonymous(self):
        variant = Variant(loc="1:65", ref="ABCDEF", alt="AAABBB")
        request = AnnotationRequestFactory.create_annotation_request(
            self.annotator, variant, self.tm
        )
        request.cod2aa = lambda codon: "Asn"
        effect = self.effect_checker.get_effect(request)
        self.assertEqual(effect.effect, "synonymous")
