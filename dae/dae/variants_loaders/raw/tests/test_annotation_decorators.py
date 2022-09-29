# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pytest

from dae.variants_loaders.raw.loader import AnnotationPipelineDecorator, \
    StoredAnnotationDecorator


@pytest.fixture
def iossifov2014_decorated(iossifov2014_loader, annotation_pipeline_internal):
    variants_loader, families_loader = iossifov2014_loader
    variants_loader = AnnotationPipelineDecorator(
        variants_loader, annotation_pipeline_internal)
    return variants_loader, families_loader


def test_gpf_instance_genomic_resources_repository(gpf_instance_2013):
    grr = gpf_instance_2013.grr
    print(grr)
    assert grr is not None


def test_annotation_pipeline_decorator_iossifov2014(iossifov2014_decorated):

    variants_loader, _families_loader = iossifov2014_decorated
    assert variants_loader.annotation_schema is not None

    for sv, _ in variants_loader.full_variants_iterator():
        assert len(sv.alt_alleles) == 1
        print(sv, sv.alt_alleles[0].attributes)

        assert sv.alt_alleles[0].attributes["score0"] == sv.position
        assert sv.alt_alleles[0].attributes["score2"] == sv.position / 100
        assert sv.alt_alleles[0].attributes["score4"] == sv.position / 10000


def test_stored_annotation_iossifov2014(iossifov2014_decorated, temp_filename):

    variants_loader, _families_loader = iossifov2014_decorated
    assert variants_loader.annotation_schema is not None

    StoredAnnotationDecorator.save_annotation_file(
        variants_loader, temp_filename
    )

    loader = StoredAnnotationDecorator(
        variants_loader, temp_filename
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
        variants_loader, temp_filename
    )

    loader = StoredAnnotationDecorator(
        variants_loader, temp_filename
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
        variants_loader, temp_filename
    )

    loader = StoredAnnotationDecorator(
        variants_loader, temp_filename
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
