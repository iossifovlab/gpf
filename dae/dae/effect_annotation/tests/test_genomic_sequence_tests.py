from .mocks import ExonMock
from .mocks import TranscriptModelMock
from .mocks import ReferenceGenomeMock
from .mocks import AnnotatorMock

from dae.effect_annotation.annotation_request import AnnotationRequestFactory
from dae.effect_annotation.annotator import Variant


def test_get_coding_left_inner():
    annotator = AnnotatorMock(ReferenceGenomeMock())
    exons = [ExonMock(50, 100, 0), ExonMock(400, 500, 2)]
    tm = TranscriptModelMock("+", 1, 2000, exons)
    gen_seq = AnnotationRequestFactory.create_annotation_request(
        annotator, None, tm
    )

    assert gen_seq.get_coding_left(98, 2, 0) == "ab"


def test_get_coding_left_cross_border():
    annotator = AnnotatorMock(ReferenceGenomeMock())
    exons = [ExonMock(50, 100, 0), ExonMock(120, 500, 2)]
    tm = TranscriptModelMock("+", 1, 2000, exons)
    gen_seq = AnnotationRequestFactory.create_annotation_request(
        annotator, None, tm
    )

    assert gen_seq.get_coding_left(120, 2, 1) == "dx"


def test_get_coding_left_cross_multiple_borders():
    annotator = AnnotatorMock(ReferenceGenomeMock())
    exons = [ExonMock(i, i, 0) for i in range(97, 120, 2)]
    tm = TranscriptModelMock("+", 1, 2000, exons)
    gen_seq = AnnotationRequestFactory.create_annotation_request(
        annotator, None, tm
    )

    assert gen_seq.get_coding_left(119, 10, 11) == "egikmoqsuw"


def test_get_coding_right_inner():
    annotator = AnnotatorMock(ReferenceGenomeMock())
    exons = [ExonMock(50, 100, 0), ExonMock(400, 500, 2)]
    tm = TranscriptModelMock("+", 1, 2000, exons)
    gen_seq = AnnotationRequestFactory.create_annotation_request(
        annotator, None, tm
    )

    assert gen_seq.get_coding_right(97, 2, 0) == "ab"


def test_get_coding_right_cross_border():
    annotator = AnnotatorMock(ReferenceGenomeMock())
    exons = [ExonMock(50, 100, 0), ExonMock(120, 500, 2)]
    tm = TranscriptModelMock("+", 1, 2000, exons)
    gen_seq = AnnotationRequestFactory.create_annotation_request(
        annotator, None, tm
    )

    assert gen_seq.get_coding_right(100, 2, 0) == "dx"


def test_get_coding_right_cross_multiple_borders():
    annotator = AnnotatorMock(ReferenceGenomeMock())
    exons = [ExonMock(i, i, 0) for i in range(97, 120, 2)]
    tm = TranscriptModelMock("+", 1, 2000, exons)
    gen_seq = AnnotationRequestFactory.create_annotation_request(
        annotator, None, tm
    )

    assert gen_seq.get_coding_right(101, 10, 2) == "egikmoqsuw"


def test_get_coding_region_for_pos():
    annotator = AnnotatorMock(ReferenceGenomeMock())
    exons = [ExonMock(i, i, 0) for i in range(97, 120, 2)]
    tm = TranscriptModelMock("+", 1, 2000, exons)
    gen_seq = AnnotationRequestFactory.create_annotation_request(
        annotator, None, tm
    )

    assert gen_seq.get_coding_region_for_pos(119) == 11


def test_invalid_get_coding_region_for_pos():
    annotator = AnnotatorMock(ReferenceGenomeMock())
    exons = [ExonMock(i, i, 0) for i in range(97, 120, 2)]
    tm = TranscriptModelMock("+", 1, 2000, exons)
    gen_seq = AnnotationRequestFactory.create_annotation_request(
        annotator, None, tm
    )

    assert gen_seq.get_coding_region_for_pos(130) is None


def test_get_frame():
    annotator = AnnotatorMock(ReferenceGenomeMock())
    exons = [
        ExonMock(50, 100, 0),
        ExonMock(200, 250, 1),
        ExonMock(400, 500, 2),
    ]
    tm = TranscriptModelMock("+", 1, 2000, exons)
    gen_seq = AnnotationRequestFactory.create_annotation_request(
        annotator, None, tm
    )

    assert gen_seq.get_frame(54, 0) == 1
    assert gen_seq.get_frame(56, 0) == 0

    assert gen_seq.get_frame(201, 1) == 2

    assert gen_seq.get_frame(401, 2) == 0


def test_get_codons():
    variant = Variant(loc="1:80", ref="-" * 15, alt="A")
    annotator = AnnotatorMock(ReferenceGenomeMock())
    exons = [ExonMock(65, 70, 0), ExonMock(80, 90, 1), ExonMock(100, 110, 2)]
    tm = TranscriptModelMock("+", 1, 2000, exons)
    gen_seq = AnnotationRequestFactory.create_annotation_request(
        annotator, variant, tm
    )
    ref_codons, alt_codons = gen_seq.get_codons()

    assert ref_codons == "FPQRSTUVWXYZdefghi"
    assert alt_codons == "FAd"
