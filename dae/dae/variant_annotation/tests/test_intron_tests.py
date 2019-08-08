import unittest
import pytest
from dae.variant_annotation.annotator import Variant
from .mocks import ExonMock
from .mocks import TranscriptModelMock
from .mocks import ReferenceGenomeMock
from .mocks import AnnotatorMock
from dae.variant_annotation.effect_checkers.intron \
    import IntronicEffectChecker
from dae.variant_annotation.annotation_request import AnnotationRequestFactory


@pytest.fixture(scope="class")
def positive_strand(request):
    request.cls.annotator = AnnotatorMock(ReferenceGenomeMock())
    exons = [ExonMock(65, 70, 0),
             ExonMock(80, 90, 1),
             ExonMock(100, 110, 2)]
    request.cls.tm = TranscriptModelMock("+", 1, 2000, exons)
    request.cls.effect_checker = IntronicEffectChecker()


@pytest.mark.usefixtures("positive_strand")
class IntronPositiveStrandTest(unittest.TestCase):
    def test_insertion_3_prime_side(self):
        variant = Variant(loc="1:80", ref="", alt="A")
        request = AnnotationRequestFactory.create_annotation_request(
            self.annotator, variant, self.tm
        )
        effect = self.effect_checker.get_effect(request)
        self.assertEqual(effect, None)

        variant = Variant(loc="1:79", ref="", alt="A")
        request = AnnotationRequestFactory.create_annotation_request(
            self.annotator, variant, self.tm
        )
        effect = self.effect_checker.get_effect(request)
        self.assertEqual(effect.effect, "intron")

        variant = Variant(loc="1:78", ref="", alt="A")
        request = AnnotationRequestFactory.create_annotation_request(
            self.annotator, variant, self.tm
        )
        effect = self.effect_checker.get_effect(request)
        self.assertEqual(effect.effect, "intron")

    def test_deletion_3_prime_side(self):
        variant = Variant(loc="1:80", ref="0", alt="")
        request = AnnotationRequestFactory.create_annotation_request(
            self.annotator, variant, self.tm
        )
        effect = self.effect_checker.get_effect(request)
        self.assertEqual(effect, None)

        variant = Variant(loc="1:79", ref="0", alt="")
        request = AnnotationRequestFactory.create_annotation_request(
            self.annotator, variant, self.tm
        )
        effect = self.effect_checker.get_effect(request)
        self.assertEqual(effect.effect, "intron")

        variant = Variant(loc="1:78", ref="0", alt="")
        request = AnnotationRequestFactory.create_annotation_request(
            self.annotator, variant, self.tm
        )
        effect = self.effect_checker.get_effect(request)
        self.assertEqual(effect.effect, "intron")

        variant = Variant(loc="1:77", ref="0", alt="")
        request = AnnotationRequestFactory.create_annotation_request(
            self.annotator, variant, self.tm
        )
        effect = self.effect_checker.get_effect(request)
        self.assertEqual(effect.effect, "intron")

    def test_subs_3_prime_side(self):
        variant = Variant(loc="1:80", ref="A", alt="G")
        request = AnnotationRequestFactory.create_annotation_request(
            self.annotator, variant, self.tm
        )
        effect = self.effect_checker.get_effect(request)
        self.assertEqual(effect, None)

        variant = Variant(loc="1:79", ref="A", alt="G")
        request = AnnotationRequestFactory.create_annotation_request(
            self.annotator, variant, self.tm
        )
        effect = self.effect_checker.get_effect(request)
        self.assertEqual(effect.effect, "intron")

        variant = Variant(loc="1:78", ref="A", alt="G")
        request = AnnotationRequestFactory.create_annotation_request(
            self.annotator, variant, self.tm
        )
        effect = self.effect_checker.get_effect(request)
        self.assertEqual(effect.effect, "intron")

        variant = Variant(loc="1:77", ref="A", alt="G")
        request = AnnotationRequestFactory.create_annotation_request(
            self.annotator, variant, self.tm
        )
        effect = self.effect_checker.get_effect(request)
        self.assertEqual(effect.effect, "intron")

    def test_insertion_5_prime_side(self):
        variant = Variant(loc="1:70", ref="", alt="A")
        request = AnnotationRequestFactory.create_annotation_request(
            self.annotator, variant, self.tm
        )
        effect = self.effect_checker.get_effect(request)
        self.assertEqual(effect, None)

        variant = Variant(loc="1:71", ref="", alt="A")
        request = AnnotationRequestFactory.create_annotation_request(
            self.annotator, variant, self.tm
        )
        effect = self.effect_checker.get_effect(request)
        self.assertEqual(effect.effect, "intron")

        variant = Variant(loc="1:72", ref="", alt="A")
        request = AnnotationRequestFactory.create_annotation_request(
            self.annotator, variant, self.tm
        )
        effect = self.effect_checker.get_effect(request)
        self.assertEqual(effect.effect, "intron")

        variant = Variant(loc="1:73", ref="", alt="A")
        request = AnnotationRequestFactory.create_annotation_request(
            self.annotator, variant, self.tm
        )
        effect = self.effect_checker.get_effect(request)
        self.assertEqual(effect.effect, "intron")

    def test_deletion_5_prime_side(self):
        variant = Variant(loc="1:70", ref="0", alt="")
        request = AnnotationRequestFactory.create_annotation_request(
            self.annotator, variant, self.tm
        )
        effect = self.effect_checker.get_effect(request)
        self.assertEqual(effect, None)

        variant = Variant(loc="1:71", ref="0", alt="")
        request = AnnotationRequestFactory.create_annotation_request(
            self.annotator, variant, self.tm
        )
        effect = self.effect_checker.get_effect(request)
        self.assertEqual(effect.effect, "intron")

        variant = Variant(loc="1:72", ref="0", alt="")
        request = AnnotationRequestFactory.create_annotation_request(
            self.annotator, variant, self.tm
        )
        effect = self.effect_checker.get_effect(request)
        self.assertEqual(effect.effect, "intron")

        variant = Variant(loc="1:73", ref="0", alt="")
        request = AnnotationRequestFactory.create_annotation_request(
            self.annotator, variant, self.tm
        )
        effect = self.effect_checker.get_effect(request)
        self.assertEqual(effect.effect, "intron")

    def test_subs_5_prime_side(self):
        variant = Variant(loc="1:70", ref="A", alt="G")
        request = AnnotationRequestFactory.create_annotation_request(
            self.annotator, variant, self.tm
        )
        effect = self.effect_checker.get_effect(request)
        self.assertEqual(effect, None)

        variant = Variant(loc="1:71", ref="A", alt="G")
        request = AnnotationRequestFactory.create_annotation_request(
            self.annotator, variant, self.tm
        )
        effect = self.effect_checker.get_effect(request)
        self.assertEqual(effect.effect, "intron")

        variant = Variant(loc="1:72", ref="A", alt="G")
        request = AnnotationRequestFactory.create_annotation_request(
            self.annotator, variant, self.tm
        )
        effect = self.effect_checker.get_effect(request)
        self.assertEqual(effect.effect, "intron")

        variant = Variant(loc="1:73", ref="A", alt="G")
        request = AnnotationRequestFactory.create_annotation_request(
            self.annotator, variant, self.tm
        )
        effect = self.effect_checker.get_effect(request)
        self.assertEqual(effect.effect, "intron")
