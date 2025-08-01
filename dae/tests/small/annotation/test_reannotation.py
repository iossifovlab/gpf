# pylint: disable=W0621,C0114,C0116,W0212,W0613


from unittest.mock import MagicMock

from dae.annotation.annotation_config import AttributeInfo
from dae.annotation.annotation_factory import adjust_for_reannotation
from dae.annotation.annotation_pipeline import (
    AnnotationPipeline,
    Annotator,
    _build_dependency_graph,
    get_deleted_attributes,
    get_rerun_annotators,
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


def test_dependency_graph_grandparent_dependency() -> None:
    # annotator can be a dependency for a child as well as grandchildren
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
    assert graph == {
        dummy_annotator_1.get_info(): [],
        dummy_annotator_2.get_info(): [
            (dummy_annotator_1.get_info(), attribute_1),
        ],
        dummy_annotator_3.get_info(): [
            (dummy_annotator_2.get_info(), attribute_2),
            (dummy_annotator_1.get_info(), attribute_1),
        ],
    }


def test_get_rerun_annotators_dependency_changed() -> None:
    attribute_1 = \
        AttributeInfo("attr_1", "attr_1", internal=False, parameters={})
    dummy_annotator_1 = DummyAnnotator([attribute_1])

    attribute_2 = \
        AttributeInfo("attr_2", "attr_2", internal=False, parameters={})
    dummy_annotator_2 = DummyAnnotator([attribute_2], dependencies=("attr_1",))

    pipeline = _make_pipeline_with([dummy_annotator_1, dummy_annotator_2])

    # should not rerun if upstream annotator hasn't changed
    rerun = get_rerun_annotators(pipeline, [])
    assert rerun == set()

    # should rerun if upstream annotator HAS changed
    rerun = get_rerun_annotators(pipeline, [dummy_annotator_1.get_info()])
    assert rerun == {
        dummy_annotator_2.get_info(),
    }


def test_get_rerun_annotators_internal_new_dependent() -> None:
    attribute_1 = \
        AttributeInfo("attr_1", "attr_1", internal=True, parameters={})
    dummy_annotator_1 = DummyAnnotator([attribute_1])

    attribute_2 = \
        AttributeInfo("attr_2", "attr_2", internal=False, parameters={})
    dummy_annotator_2 = DummyAnnotator([attribute_2], dependencies=("attr_1",))

    pipeline = _make_pipeline_with([dummy_annotator_1, dummy_annotator_2])

    # should rerun if internal and a new dependent has been added downstream
    rerun = get_rerun_annotators(pipeline, [dummy_annotator_2.get_info()])
    assert rerun == {
        dummy_annotator_1.get_info(),
    }


def test_get_rerun_annotators_internal_dependent_rerun() -> None:
    attribute_1 = \
        AttributeInfo("attr_1", "attr_1", internal=True, parameters={})
    dummy_annotator_1 = DummyAnnotator([attribute_1])

    attribute_2 = \
        AttributeInfo("attr_2", "attr_2", internal=True, parameters={})
    dummy_annotator_2 = DummyAnnotator([attribute_2], dependencies=("attr_1",))

    attribute_3 = \
        AttributeInfo("attr_3", "attr_3", internal=False, parameters={})
    dummy_annotator_3 = DummyAnnotator([attribute_3], dependencies=("attr_2",))

    pipeline = _make_pipeline_with([dummy_annotator_1,
                                    dummy_annotator_2,
                                    dummy_annotator_3])

    # should rerun if internal (annotator 1) and a downstream
    # annotator is rerun (annotator 2)
    rerun = get_rerun_annotators(pipeline, [dummy_annotator_3.get_info()])
    assert rerun == {
        dummy_annotator_2.get_info(),
        dummy_annotator_1.get_info(),
    }


def test_get_rerun_annotators_non_internal_new_dependent() -> None:
    attribute_1 = \
        AttributeInfo("attr_1", "attr_1", internal=False, parameters={})
    dummy_annotator_1 = DummyAnnotator([attribute_1])

    attribute_2 = \
        AttributeInfo("attr_2", "attr_2", internal=False, parameters={})
    dummy_annotator_2 = DummyAnnotator([attribute_2], dependencies=("attr_1",))

    pipeline = _make_pipeline_with([dummy_annotator_1, dummy_annotator_2])

    # should not rerun if not internal and dependent is new
    rerun = get_rerun_annotators(pipeline, [dummy_annotator_2.get_info()])
    assert rerun == set()


def test_get_rerun_annotators_non_internal_rerun_dependent() -> None:
    attribute_1 = \
        AttributeInfo("attr_1", "attr_1", internal=False, parameters={})
    dummy_annotator_1 = DummyAnnotator([attribute_1])

    attribute_2 = \
        AttributeInfo("attr_2", "attr_2", internal=True, parameters={})
    dummy_annotator_2 = DummyAnnotator([attribute_2], dependencies=("attr_1",))

    attribute_3 = \
        AttributeInfo("attr_3", "attr_3", internal=False, parameters={})
    dummy_annotator_3 = DummyAnnotator([attribute_3], dependencies=("attr_2",))

    pipeline = _make_pipeline_with([dummy_annotator_1,
                                    dummy_annotator_2,
                                    dummy_annotator_3])

    # shouldn't rerun if not internal (annotator 1) and a downstream
    # annotator is rerun (annotator 2)
    rerun = get_rerun_annotators(pipeline, [dummy_annotator_3.get_info()])
    assert rerun == {
        dummy_annotator_2.get_info(),
    }


def test_get_deleted_attributes() -> None:
    # attribute deleted in new pipeline
    attribute_1 = \
        AttributeInfo("attr_1", "attr_1", internal=False, parameters={})
    dummy_annotator_1 = DummyAnnotator([attribute_1])

    attribute_2 = \
        AttributeInfo("attr_2", "attr_2", internal=False, parameters={})
    dummy_annotator_2 = DummyAnnotator([attribute_2])

    old_pipeline = _make_pipeline_with([dummy_annotator_1])
    new_pipeline = _make_pipeline_with([dummy_annotator_2])

    assert get_deleted_attributes(new_pipeline, old_pipeline) == ["attr_1"]


def test_get_deleted_attributes_shared_name() -> None:
    # new attribute in new pipeline shares name with old - must still delete
    attribute_1 = \
        AttributeInfo("attr_1", "attr_1", internal=False, parameters={})
    dummy_annotator_1 = DummyAnnotator([attribute_1])

    attribute_2 = \
        AttributeInfo("attr_1", "attr_2", internal=False, parameters={})
    dummy_annotator_2 = DummyAnnotator([attribute_2])

    old_pipeline = _make_pipeline_with([dummy_annotator_1])
    new_pipeline = _make_pipeline_with([dummy_annotator_2])

    assert get_deleted_attributes(new_pipeline, old_pipeline) == ["attr_1"]


def test_get_deleted_attributes_ignore_internal() -> None:
    # don't try to delete internal attributes
    attribute_1 = \
        AttributeInfo("attr_1", "attr_1", internal=True, parameters={})
    dummy_annotator_1 = DummyAnnotator([attribute_1])

    attribute_2 = \
        AttributeInfo("attr_2", "attr_2", internal=False, parameters={})
    dummy_annotator_2 = DummyAnnotator([attribute_2])

    old_pipeline = _make_pipeline_with([dummy_annotator_1])
    new_pipeline = _make_pipeline_with([dummy_annotator_2])

    assert not get_deleted_attributes(new_pipeline, old_pipeline)


def test_get_deleted_attributes_full_reannotation() -> None:
    # full reannotation - delete all
    attribute_1 = \
        AttributeInfo("attr_1", "attr_1", internal=True, parameters={})
    dummy_annotator_1 = DummyAnnotator([attribute_1])

    attribute_2 = \
        AttributeInfo("attr_2", "attr_2", internal=False, parameters={})
    dummy_annotator_2 = DummyAnnotator([attribute_2])

    old_pipeline = _make_pipeline_with([dummy_annotator_1, dummy_annotator_2])
    new_pipeline = _make_pipeline_with([dummy_annotator_1, dummy_annotator_2])

    assert get_deleted_attributes(
        new_pipeline, old_pipeline, full_reannotation=True,
    ) == ["attr_1", "attr_2"]


def test_adjust_for_reannotation() -> None:
    attribute_1 = \
        AttributeInfo("attr_1", "attr_1", internal=False, parameters={})
    dummy_annotator_1 = DummyAnnotator([attribute_1])

    attribute_2 = \
        AttributeInfo("attr_2", "attr_2", internal=True, parameters={})
    dummy_annotator_2 = DummyAnnotator([attribute_2], dependencies=("attr_1",))

    attribute_3 = \
        AttributeInfo("attr_3", "attr_3", internal=False, parameters={})
    dummy_annotator_3 = DummyAnnotator([attribute_3], dependencies=("attr_2",))

    old_pipeline = _make_pipeline_with(
        [dummy_annotator_1, dummy_annotator_2])

    new_pipeline = _make_pipeline_with(
        [dummy_annotator_1, dummy_annotator_2, dummy_annotator_3])

    adjust_for_reannotation(new_pipeline, old_pipeline)

    assert new_pipeline.subset_to_run == [
        # annotator subset to run should have all rerun annotators
        dummy_annotator_2,
        # annotator subset to run should have all new annotators
        dummy_annotator_3,
    ]
