# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pytest

from dae.import_tools.annotation_decorators import (
    AnnotationPipelineDecorator,
)


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
