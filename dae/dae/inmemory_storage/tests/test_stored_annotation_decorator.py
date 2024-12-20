# pylint: disable=W0621,C0114,C0116,W0212,W0613

import pytest

from dae.import_tools.annotation_decorators import AnnotationPipelineDecorator
from dae.inmemory_storage.stored_annotation_decorator import (
    StoredAnnotationDecorator,
)


@pytest.fixture
def iossifov2014_decorated(iossifov2014_loader, annotation_pipeline_internal):
    variants_loader, families_loader = iossifov2014_loader
    variants_loader = AnnotationPipelineDecorator(
        variants_loader, annotation_pipeline_internal)
    return variants_loader, families_loader


@pytest.mark.parametrize(
    "filename,annotation",
    [
        ("vcf.vcf", "vcf-vcf-eff.txt"),
        ("vcf", "vcf-eff.txt"),
        ("vcf.vcf.gz", "vcf-vcf-gz-eff.txt"),
    ],
)
def test_build_annotation_filename(filename, annotation):

    assert (
        StoredAnnotationDecorator.build_annotation_filename(filename)
        == annotation
    )


def test_stored_annotation_iossifov2014(iossifov2014_decorated, temp_filename):

    variants_loader, _families_loader = iossifov2014_decorated
    assert variants_loader.annotation_schema is not None

    StoredAnnotationDecorator.save_annotation_file(
        variants_loader, temp_filename,
    )

    loader = StoredAnnotationDecorator(
        variants_loader, temp_filename,
    )

    for sv, _ in loader.full_variants_iterator():
        assert len(sv.alt_alleles) == 1
        print(sv, sv.alt_alleles[0].attributes)

        assert sv.alt_alleles[0].attributes["score0"] == sv.position, \
            sv.alt_alleles[0].attributes
        assert sv.alt_alleles[0].attributes["score2"] == sv.position / 100, \
            sv.alt_alleles[0].attributes
        assert sv.alt_alleles[0].attributes["score4"] == sv.position / 10000, \
            sv.alt_alleles[0].attributes


def test_stored_annotation_does_not_change_summary_alleles(
        iossifov2014_decorated, temp_filename):
    variants_loader, _families_loader = iossifov2014_decorated
    assert variants_loader.annotation_schema is not None

    StoredAnnotationDecorator.save_annotation_file(
        variants_loader, temp_filename,
    )

    loader = StoredAnnotationDecorator(
        variants_loader, temp_filename,
    )

    for _sv, fvs in loader.full_variants_iterator():
        for fv in fvs:
            # Effects will be None if the annotator copies the summary allele
            assert fv.effects is not None


def test_stored_annotation_saves_nonetype_properly(
        iossifov2014_decorated, temp_filename):

    variants_loader, _families_loader = iossifov2014_decorated
    assert variants_loader.annotation_schema is not None

    StoredAnnotationDecorator.save_annotation_file(
        variants_loader, temp_filename,
    )

    loader = StoredAnnotationDecorator(
        variants_loader, temp_filename,
    )

    for sv, _ in loader.full_variants_iterator():
        assert len(sv.alt_alleles) == 1
        if sv.chromosome == "3":
            assert sv.alt_alleles[0].attributes[
                "score0_incomplete_cov"
            ] is None
        else:
            assert sv.alt_alleles[0].attributes["score0_incomplete_cov"] == \
                float(sv.position)
