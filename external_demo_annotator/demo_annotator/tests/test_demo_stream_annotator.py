# pylint: disable=W0621,C0114,C0116,W0212,W0613
import textwrap

import pytest

from dae.annotation.annotate_utils import AnnotationTool
from demo_annotator.adapter import DemoAnnotatorAdapter


@pytest.fixture()
def config_1() -> str:
    return textwrap.dedent("""
        - external_demo_stream_annotator
    """)


@pytest.fixture()
def config_2() -> str:
    return textwrap.dedent("""
        - external_demo_stream_annotator: {}
    """)


@pytest.fixture()
def config_3() -> str:
    return textwrap.dedent("""
        - external_demo_stream_annotator:
            attributes:
            - name: annotatable_length
    """)


@pytest.fixture()
def config_4() -> str:
    return textwrap.dedent("""
        - external_demo_stream_annotator:
            attributes:
            - name: pesho
              source: annotatable_length
    """)


@pytest.fixture()
def config_5() -> str:
    return textwrap.dedent("""
        - external_demo_stream_annotator:
            attributes:
            - name: pesho
              source: annotatable_length
            - name: gosho
              source: annotatable_length
    """)


@pytest.fixture()
def annotation_configs(
    config_1: str,
    config_2: str,
    config_3: str,
    config_4: str,
    config_5: str,
) -> dict[str]:
    return {
        "config_1": config_1,
        "config_2": config_2,
        "config_3": config_3,
        "config_4": config_4,
        "config_5": config_5,
    }


@pytest.mark.parametrize(
    "config_key",
    [
        ("config_1"),
        ("config_2"),
        ("config_3"),
        ("config_4"),
        ("config_5"),
    ]
)
def test_demo_annotator_initialization(annotation_configs, config_key):
    config = annotation_configs[config_key]
    pipeline = AnnotationTool._produce_annotation_pipeline(
        config, None, None, allow_repeated_attributes=True
    )
    annotators = pipeline.annotators
    assert len(annotators) == 1
    assert isinstance(annotators[0], DemoAnnotatorAdapter)
