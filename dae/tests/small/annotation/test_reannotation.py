# pylint: disable=W0621,C0114,C0116,W0212,W0613


from unittest.mock import MagicMock

from dae.annotation.annotation_config import AttributeInfo
from dae.annotation.annotation_pipeline import (
    AnnotationPipeline,
    Annotator,
    _build_dependency_graph,
    _get_dependencies_for,
    _get_dependents_of,
)

from tests.small.annotation.conftest import DummyAnnotator


def _make_pipeline_with(
    annotators: list[Annotator],
) -> AnnotationPipeline:
    pipeline = AnnotationPipeline(MagicMock())
    for annotator in annotators:
        pipeline.add_annotator(annotator)
    return pipeline


def test_dependency_graph_empty() -> None:
    # empty graph
    pipeline = _make_pipeline_with([])
    graph = _build_dependency_graph(pipeline)
    assert not graph


def test_dependency_graph_no_dependencies() -> None:
    # annotator can depend on nothing
    dummy_annotator_1 = DummyAnnotator(
        [AttributeInfo("attr_1", "attr_1", internal=False, parameters={})],
    )
    dummy_annotator_2 = DummyAnnotator(
        [AttributeInfo("attr_2", "attr_2", internal=False, parameters={})],
    )
    pipeline = _make_pipeline_with([dummy_annotator_1, dummy_annotator_2])
    graph = _build_dependency_graph(pipeline)
    assert graph == {
        dummy_annotator_1.get_info(): [],
        dummy_annotator_2.get_info(): [],
    }


def test_dependency_graph_one_dependency() -> None:
    # annotator can depend on one annotator
    attribute_1 = \
        AttributeInfo("attr_1", "attr_1", internal=False, parameters={})
    dummy_annotator_1 = DummyAnnotator([attribute_1])

    attribute_2 = \
        AttributeInfo("attr_2", "attr_2", internal=False, parameters={})
    dummy_annotator_2 = DummyAnnotator([attribute_2], dependencies=("attr_1",))

    pipeline = _make_pipeline_with([dummy_annotator_1, dummy_annotator_2])
    graph = _build_dependency_graph(pipeline)
    assert graph == {
        dummy_annotator_1.get_info(): [],
        dummy_annotator_2.get_info(): [
            (dummy_annotator_1.get_info(), attribute_1),
        ],
    }


def test_dependency_graph_multiple_dependencies() -> None:
    # annotator can depend on multiple annotators
    attribute_1 = \
        AttributeInfo("attr_1", "attr_1", internal=False, parameters={})
    dummy_annotator_1 = DummyAnnotator([attribute_1])

    attribute_2 = \
        AttributeInfo("attr_2", "attr_2", internal=False, parameters={})
    dummy_annotator_2 = DummyAnnotator([attribute_2])

    attribute_3 = \
        AttributeInfo("attr_3", "attr_3", internal=False, parameters={})
    dummy_annotator_3 = DummyAnnotator([attribute_3],
                                       dependencies=("attr_1", "attr_2"))

    pipeline = _make_pipeline_with([dummy_annotator_1,
                                    dummy_annotator_2,
                                    dummy_annotator_3])
    graph = _build_dependency_graph(pipeline)
    assert graph == {
        dummy_annotator_1.get_info(): [],
        dummy_annotator_2.get_info(): [],
        dummy_annotator_3.get_info(): [
            (dummy_annotator_1.get_info(), attribute_1),
            (dummy_annotator_2.get_info(), attribute_2),
        ],
    }


def test_dependency_graph_dependency_for_many() -> None:
    # annotator can be a dependency for multiple annotators
    attribute_1 = \
        AttributeInfo("attr_1", "attr_1", internal=False, parameters={})
    dummy_annotator_1 = DummyAnnotator([attribute_1])

    attribute_2 = \
        AttributeInfo("attr_2", "attr_2", internal=False, parameters={})
    dummy_annotator_2 = DummyAnnotator([attribute_2], dependencies=("attr_1",))

    attribute_3 = \
        AttributeInfo("attr_3", "attr_3", internal=False, parameters={})
    dummy_annotator_3 = DummyAnnotator([attribute_3], dependencies=("attr_1",))

    pipeline = _make_pipeline_with([dummy_annotator_1,
                                    dummy_annotator_2,
                                    dummy_annotator_3])
    graph = _build_dependency_graph(pipeline)
    assert graph == {
        dummy_annotator_1.get_info(): [],
        dummy_annotator_2.get_info(): [
            (dummy_annotator_1.get_info(), attribute_1),
        ],
        dummy_annotator_3.get_info(): [
            (dummy_annotator_1.get_info(), attribute_1),
        ],
    }


def test_get_dependencies_for_nothing() -> None:
    # zero dependencies
    attribute_1 = \
        AttributeInfo("attr_1", "attr_1", internal=False, parameters={})
    dummy_annotator_1 = DummyAnnotator([attribute_1])

    attribute_2 = \
        AttributeInfo("attr_2", "attr_2", internal=False, parameters={})
    dummy_annotator_2 = DummyAnnotator([attribute_2])

    pipeline = _make_pipeline_with([dummy_annotator_1, dummy_annotator_2])
    graph = _build_dependency_graph(pipeline)

    assert _get_dependencies_for(dummy_annotator_1.get_info(), graph) == set()
    assert _get_dependencies_for(dummy_annotator_2.get_info(), graph) == set()


def test_get_dependencies_for_singular() -> None:
    # one dependency
    attribute_1 = \
        AttributeInfo("attr_1", "attr_1", internal=False, parameters={})
    dummy_annotator_1 = DummyAnnotator([attribute_1])

    attribute_2 = \
        AttributeInfo("attr_2", "attr_2", internal=False, parameters={})
    dummy_annotator_2 = DummyAnnotator([attribute_2], dependencies=("attr_1",))

    pipeline = _make_pipeline_with([dummy_annotator_1, dummy_annotator_2])
    graph = _build_dependency_graph(pipeline)

    assert _get_dependencies_for(dummy_annotator_1.get_info(), graph) == set()
    assert _get_dependencies_for(dummy_annotator_2.get_info(), graph) == {
        dummy_annotator_1.get_info(),
    }


def test_get_dependencies_for_multiple_flat() -> None:
    # two dependencies - two parents (flat)
    attribute_1 = \
        AttributeInfo("attr_1", "attr_1", internal=False, parameters={})
    dummy_annotator_1 = DummyAnnotator([attribute_1])

    attribute_2 = \
        AttributeInfo("attr_2", "attr_2", internal=False, parameters={})
    dummy_annotator_2 = DummyAnnotator([attribute_2])

    attribute_3 = \
        AttributeInfo("attr_3", "attr_3", internal=False, parameters={})
    dummy_annotator_3 = DummyAnnotator([attribute_3],
                                       dependencies=("attr_1", "attr_2"))

    pipeline = _make_pipeline_with([dummy_annotator_1,
                                    dummy_annotator_2,
                                    dummy_annotator_3])
    graph = _build_dependency_graph(pipeline)

    assert _get_dependencies_for(dummy_annotator_1.get_info(), graph) == set()
    assert _get_dependencies_for(dummy_annotator_2.get_info(), graph) == set()
    assert _get_dependencies_for(dummy_annotator_3.get_info(), graph) == {
        dummy_annotator_1.get_info(),
        dummy_annotator_2.get_info(),
    }


def test_get_dependencies_for_multiple_recursive() -> None:
    # two dependencies - parent and grandparent (recursive)
    attribute_1 = \
        AttributeInfo("attr_1", "attr_1", internal=False, parameters={})
    dummy_annotator_1 = DummyAnnotator([attribute_1])

    attribute_2 = \
        AttributeInfo("attr_2", "attr_2", internal=False, parameters={})
    dummy_annotator_2 = DummyAnnotator([attribute_2], dependencies=("attr_1",))

    attribute_3 = \
        AttributeInfo("attr_3", "attr_3", internal=False, parameters={})
    dummy_annotator_3 = DummyAnnotator([attribute_3], dependencies=("attr_2",))

    pipeline = _make_pipeline_with([dummy_annotator_1,
                                    dummy_annotator_2,
                                    dummy_annotator_3])
    graph = _build_dependency_graph(pipeline)

    assert _get_dependencies_for(dummy_annotator_1.get_info(), graph) == set()
    assert _get_dependencies_for(dummy_annotator_2.get_info(), graph) == {
        dummy_annotator_1.get_info(),
    }
    assert _get_dependencies_for(dummy_annotator_3.get_info(), graph) == {
        dummy_annotator_1.get_info(),
        dummy_annotator_2.get_info(),
    }


def test_get_dependents_of_nothing() -> None:
    # zero dependents
    attribute_1 = \
        AttributeInfo("attr_1", "attr_1", internal=False, parameters={})
    dummy_annotator_1 = DummyAnnotator([attribute_1])

    attribute_2 = \
        AttributeInfo("attr_2", "attr_2", internal=False, parameters={})
    dummy_annotator_2 = DummyAnnotator([attribute_2])

    pipeline = _make_pipeline_with([dummy_annotator_1, dummy_annotator_2])
    graph = _build_dependency_graph(pipeline)

    assert _get_dependents_of(dummy_annotator_1.get_info(), graph) == set()
    assert _get_dependents_of(dummy_annotator_2.get_info(), graph) == set()


def test_get_dependents_of_singular() -> None:
    # one dependent
    attribute_1 = \
        AttributeInfo("attr_1", "attr_1", internal=False, parameters={})
    dummy_annotator_1 = DummyAnnotator([attribute_1])

    attribute_2 = \
        AttributeInfo("attr_2", "attr_2", internal=False, parameters={})
    dummy_annotator_2 = DummyAnnotator([attribute_2], dependencies=("attr_1",))

    pipeline = _make_pipeline_with([dummy_annotator_1, dummy_annotator_2])
    graph = _build_dependency_graph(pipeline)

    assert _get_dependents_of(dummy_annotator_1.get_info(), graph) == {
        dummy_annotator_2.get_info(),
    }
    assert _get_dependents_of(dummy_annotator_2.get_info(), graph) == set()


def test_get_dependents_of_multiple_flat() -> None:
    # two dependents - two children (flat)
    attribute_1 = \
        AttributeInfo("attr_1", "attr_1", internal=False, parameters={})
    dummy_annotator_1 = DummyAnnotator([attribute_1])

    attribute_2 = \
        AttributeInfo("attr_2", "attr_2", internal=False, parameters={})
    dummy_annotator_2 = DummyAnnotator([attribute_2], dependencies=("attr_1",))

    attribute_3 = \
        AttributeInfo("attr_3", "attr_3", internal=False, parameters={})
    dummy_annotator_3 = DummyAnnotator([attribute_3], dependencies=("attr_1",))

    pipeline = _make_pipeline_with([dummy_annotator_1,
                                    dummy_annotator_2,
                                    dummy_annotator_3])
    graph = _build_dependency_graph(pipeline)

    assert _get_dependents_of(dummy_annotator_1.get_info(), graph) == {
        dummy_annotator_2.get_info(),
        dummy_annotator_3.get_info(),
    }
    assert _get_dependents_of(dummy_annotator_2.get_info(), graph) == set()
    assert _get_dependents_of(dummy_annotator_3.get_info(), graph) == set()


def test_get_dependents_of_multiple_recursive() -> None:
    # two dependents - child and grandchild (recursive)
    attribute_1 = \
        AttributeInfo("attr_1", "attr_1", internal=False, parameters={})
    dummy_annotator_1 = DummyAnnotator([attribute_1])

    attribute_2 = \
        AttributeInfo("attr_2", "attr_2", internal=False, parameters={})
    dummy_annotator_2 = DummyAnnotator([attribute_2], dependencies=("attr_1",))

    attribute_3 = \
        AttributeInfo("attr_3", "attr_3", internal=False, parameters={})
    dummy_annotator_3 = DummyAnnotator([attribute_3], dependencies=("attr_2",))

    pipeline = _make_pipeline_with([dummy_annotator_1,
                                    dummy_annotator_2,
                                    dummy_annotator_3])
    graph = _build_dependency_graph(pipeline)

    assert _get_dependents_of(dummy_annotator_1.get_info(), graph) == {
        dummy_annotator_2.get_info(),
        dummy_annotator_3.get_info(),
    }
    assert _get_dependents_of(dummy_annotator_2.get_info(), graph) == {
        dummy_annotator_3.get_info(),
    }
    assert _get_dependents_of(dummy_annotator_3.get_info(), graph) == set()


def test_get_rerun_annotators() -> None:
    # should rerun if dependency is new
    # should not rerun if dependency is only rerun

    # should rerun if internal and dependent is new
    # should rerun if internal and dependent is rerun

    # should not rerun if not internal and dependent is new
    # should not rerun if not internal and dependent is rerun
    pass


def test_get_deleted_attributes() -> None:
    # attribute deleted in new pipeline
    # attribute completely changed in new pipeline - still delete from old
    pass


def test_adjust_for_reannotation() -> None:
    # annotator subset to run should have all new annotators
    # annotator subset to run should have all rerun annotators
    pass
