import pytest

from dae.annotation.annotation_factory import AnnotationConfigurationError
from dae.annotation.annotation_factory import build_annotation_pipeline
from dae.genomic_resources.testing import build_inmemory_test_repository


def test_pipeline_not_a_list():
    with pytest.raises(AnnotationConfigurationError, match="not a list"):
        build_annotation_pipeline(pipeline_config_str="""
            debug_annotator
            """, grr_repository=build_inmemory_test_repository({}))


def test_pipeline_repeated_annotator_attribute():
    with pytest.raises(AnnotationConfigurationError, match="attributes: hi"):
        build_annotation_pipeline(pipeline_config_str="""
            - debug_annotator:
                attributes:
                - hi
                - hi
            """, grr_repository=build_inmemory_test_repository({}))


def test_pipeline_repeated_attribute():
    with pytest.raises(AnnotationConfigurationError, match="attributes hi"):
        build_annotation_pipeline(pipeline_config_str="""
            - debug_annotator:
                attributes:
                - hi
            - debug_annotator:
                attributes:
                - hi
            """, grr_repository=build_inmemory_test_repository({}))


def test_pipeline_annoing_identation_error():
    with pytest.raises(AnnotationConfigurationError,
                       match="Incorrect annotator configuation form"):
        build_annotation_pipeline(pipeline_config_str="""
            - debug_annotator:
              attributes:
                - hi
            """, grr_repository=build_inmemory_test_repository({}))
