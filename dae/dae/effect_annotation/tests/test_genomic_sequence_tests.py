# pylint: disable=W0621,C0114,C0116,W0212,W0613
from typing import cast

from dae.genomic_resources.gene_models import Exon, TranscriptModel
from dae.effect_annotation.annotator import AnnotationRequestFactory, \
    EffectAnnotator
from dae.effect_annotation.annotator import Variant

from .mocks import TranscriptModelMock


def test_get_coding_left_inner(annotator: EffectAnnotator) -> None:
    exons = [Exon(50, 100, 0), Exon(400, 500, 2)]
    transcript_model = cast(
        TranscriptModel, TranscriptModelMock("+", 1, 2000, exons))
    gen_seq = AnnotationRequestFactory.create_annotation_request(
        annotator, None, transcript_model  # type: ignore
    )

    assert gen_seq.get_coding_left(98, 2, 0) == "ab"


def test_get_coding_left_cross_border(annotator: EffectAnnotator) -> None:
    exons = [Exon(50, 100, 0), Exon(120, 500, 2)]
    transcript_model = cast(
        TranscriptModel, TranscriptModelMock("+", 1, 2000, exons))
    gen_seq = AnnotationRequestFactory.create_annotation_request(
        annotator, None, transcript_model  # type: ignore
    )

    assert gen_seq.get_coding_left(120, 2, 1) == "dx"


def test_get_coding_left_cross_multiple_borders(
    annotator: EffectAnnotator
) -> None:
    exons = [Exon(i, i, 0) for i in range(97, 120, 2)]
    transcript_model = cast(
        TranscriptModel, TranscriptModelMock("+", 1, 2000, exons))
    gen_seq = AnnotationRequestFactory.create_annotation_request(
        annotator, None, transcript_model  # type: ignore
    )

    assert gen_seq.get_coding_left(119, 10, 11) == "egikmoqsuw"


def test_get_coding_right_inner(annotator: EffectAnnotator) -> None:
    exons = [Exon(50, 100, 0), Exon(400, 500, 2)]
    transcript_model = cast(
        TranscriptModel, TranscriptModelMock("+", 1, 2000, exons))
    gen_seq = AnnotationRequestFactory.create_annotation_request(
        annotator, None, transcript_model  # type: ignore
    )

    assert gen_seq.get_coding_right(97, 2, 0) == "ab"


def test_get_coding_right_cross_border(annotator: EffectAnnotator) -> None:
    exons = [Exon(50, 100, 0), Exon(120, 500, 2)]
    transcript_model = cast(
        TranscriptModel, TranscriptModelMock("+", 1, 2000, exons))
    gen_seq = AnnotationRequestFactory.create_annotation_request(
        annotator, None, transcript_model  # type: ignore
    )

    assert gen_seq.get_coding_right(100, 2, 0) == "dx"


def test_get_coding_right_cross_multiple_borders(
    annotator: EffectAnnotator
) -> None:
    exons = [Exon(i, i, 0) for i in range(97, 120, 2)]
    transcript_model = TranscriptModelMock("+", 1, 2000, exons)
    gen_seq = AnnotationRequestFactory.create_annotation_request(
        annotator, None, transcript_model  # type: ignore
    )

    assert gen_seq.get_coding_right(101, 10, 2) == "egikmoqsuw"


def test_get_coding_region_for_pos(annotator: EffectAnnotator) -> None:
    exons = [Exon(i, i, 0) for i in range(97, 120, 2)]
    transcript_model = cast(
        TranscriptModel, TranscriptModelMock("+", 1, 2000, exons))
    gen_seq = AnnotationRequestFactory.create_annotation_request(
        annotator, None, transcript_model  # type: ignore
    )

    assert gen_seq.get_coding_region_for_pos(119) == 11


def test_invalid_get_coding_region_for_pos(annotator: EffectAnnotator) -> None:
    exons = [Exon(i, i, 0) for i in range(97, 120, 2)]
    transcript_model = cast(
        TranscriptModel, TranscriptModelMock("+", 1, 2000, exons))
    gen_seq = AnnotationRequestFactory.create_annotation_request(
        annotator, None, transcript_model  # type: ignore
    )

    assert gen_seq.get_coding_region_for_pos(130) is None


def test_get_frame(annotator: EffectAnnotator) -> None:
    exons = [
        Exon(50, 100, 0),
        Exon(200, 250, 1),
        Exon(400, 500, 2),
    ]
    transcript_model = cast(
        TranscriptModel, TranscriptModelMock("+", 1, 2000, exons))
    gen_seq = AnnotationRequestFactory.create_annotation_request(
        annotator, None, transcript_model  # type: ignore
    )

    assert gen_seq.get_frame(54, 0) == 1
    assert gen_seq.get_frame(56, 0) == 0

    assert gen_seq.get_frame(201, 1) == 2

    assert gen_seq.get_frame(401, 2) == 0


def test_get_codons(annotator: EffectAnnotator) -> None:
    variant = Variant(loc="1:80", ref="-" * 15, alt="A")
    exons = [Exon(65, 70, 0), Exon(80, 90, 1), Exon(100, 110, 2)]
    transcript_model = cast(
        TranscriptModel, TranscriptModelMock("+", 1, 2000, exons))
    gen_seq = AnnotationRequestFactory.create_annotation_request(
        annotator, variant, transcript_model
    )
    ref_codons, alt_codons = gen_seq.get_codons()

    assert ref_codons == "FPQRSTUVWXYZdefghi"
    assert alt_codons == "FAd"
