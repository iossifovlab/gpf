import pytest

from dae.annotation.annotation_factory import (
    AnnotationConfigurationError,
    load_pipeline_from_yaml,
)
from dae.genomic_resources.testing import build_inmemory_test_repository


def test_pipeline_not_a_list() -> None:
    with pytest.raises(AnnotationConfigurationError):
        load_pipeline_from_yaml("""
            debug_annotator
            """, build_inmemory_test_repository({}))


def test_pipeline_repeated_annotator_attribute() -> None:
    with pytest.raises(AnnotationConfigurationError, match="attributes: hi"):
        load_pipeline_from_yaml("""
            - debug_annotator:
                attributes:
                - hi
                - hi
            """, build_inmemory_test_repository({}))


def test_pipeline_repeated_attribute() -> None:
    with pytest.raises(AnnotationConfigurationError, match="hi"):
        load_pipeline_from_yaml("""
            - debug_annotator:
                attributes:
                - hi
            - debug_annotator:
                attributes:
                - hi
            """, build_inmemory_test_repository({}))


def test_pipeline_annoing_identation_error() -> None:
    with pytest.raises(AnnotationConfigurationError,
                       match="Incorrect annotator configuation form"):
        load_pipeline_from_yaml("""
            - debug_annotator:
              attributes:
                - hi
            """, build_inmemory_test_repository({}))
