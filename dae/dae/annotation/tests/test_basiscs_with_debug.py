# pylint: disable=W0621,C0114,C0116,W0212,W0613

from dae.annotation.annotatable import Position
from dae.annotation.annotation_factory import load_pipeline_from_yaml
from dae.genomic_resources.testing import build_inmemory_test_repository


def test_default_attributes() -> None:
    empty_grr = build_inmemory_test_repository({})
    config = """
    - debug_annotator
    """
    pipeline = load_pipeline_from_yaml(config, empty_grr)

    info = pipeline.get_info()
    assert len(info) == 1
    assert info[0].type == "debug_annotator"
    assert len(info[0].attributes) == 1
    assert info[0].attributes[0].name == "hi"
    assert info[0].attributes[0].source == "hi"
    assert info[0].attributes[0].type == "str"

    annotation = pipeline.annotate(Position("1", 3))
    assert annotation["hi"] == "hello world"


def test_default_remapping() -> None:
    empty_grr = build_inmemory_test_repository({})
    config = """
    - debug_annotator:
        attributes:
          - hi
          - name: hi2
            source: hi
          - name: hi3
            source: hi
    """
    pipeline = load_pipeline_from_yaml(config, empty_grr)

    info = pipeline.get_info()
    assert len(info) == 1
    assert info[0].type == "debug_annotator"
    assert len(info[0].attributes) == 3
    assert info[0].attributes[1].name == "hi2"
    assert info[0].attributes[1].source == "hi"
    assert info[0].attributes[1].type == "str"

    annotation = pipeline.annotate(Position("1", 3))
    assert annotation["hi"] == "hello world"
    assert annotation["hi2"] == "hello world"
    assert annotation["hi3"] == "hello world"


def test_str_value_trasform() -> None:
    empty_grr = build_inmemory_test_repository({})
    config = """
    - debug_annotator:
        attributes:
          - hi
          - name: hi_gosho
            source: hi
            value_transform: value + ' gosho'
          - name: hi_len
            source: hi
            value_transform: len(value)
    """
    pipeline = load_pipeline_from_yaml(config, empty_grr)

    info = pipeline.get_info()
    assert len(info) == 1
    assert info[0].type == "debug_annotator"
    assert len(info[0].attributes) == 3
    assert info[0].attributes[1].name == "hi_gosho"
    assert info[0].attributes[1].parameters["value_transform"] == \
        "value + ' gosho'"
    assert info[0].attributes[1].type == "str"

    annotation = pipeline.annotate(Position("1", 3))
    assert annotation["hi"] == "hello world"
    assert annotation["hi_gosho"] == "hello world gosho"
    assert annotation["hi_len"] == 11
