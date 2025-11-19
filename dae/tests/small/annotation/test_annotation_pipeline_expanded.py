# pylint: disable=W0621,C0114,C0116,W0212,W0613
"""Comprehensive tests for annotation_pipeline module."""
from typing import Any
from unittest.mock import Mock

import pytest
from dae.annotation.annotatable import Annotatable, Position
from dae.annotation.annotation_config import AnnotatorInfo, AttributeInfo
from dae.annotation.annotation_pipeline import (
    AnnotationPipeline,
    Annotator,
    InputAnnotableAnnotatorDecorator,
    ReannotationPipeline,
    ValueTransformAnnotatorDecorator,
    _build_dependency_graph,
    _get_deleted_attributes,
    _get_dependencies_for,
    _get_rerun_annotators,
)
from dae.genomic_resources.repository import GenomicResourceRepo
from dae.genomic_resources.testing import build_inmemory_test_repository

from tests.small.annotation.conftest import DummyAnnotator


def make_attr(
    name: str, source: str | None = None, *,
    internal: bool | None = None,
    **kwargs: Any,
) -> AttributeInfo:
    """Helper to create AttributeInfo with defaults."""
    if source is None:
        source = name
    return AttributeInfo(
        name, source, internal=internal,
        parameters=kwargs or {})


@pytest.fixture
def test_repo() -> GenomicResourceRepo:
    """Create test repository."""
    return build_inmemory_test_repository({})


@pytest.fixture
def basic_pipeline(test_repo: GenomicResourceRepo) -> AnnotationPipeline:
    """Create basic annotation pipeline."""
    return AnnotationPipeline(test_repo)


# Tests for _build_dependency_graph

def test_build_dependency_graph_empty_pipeline(
    basic_pipeline: AnnotationPipeline,
) -> None:
    """Test dependency graph for empty pipeline."""
    graph = _build_dependency_graph(basic_pipeline)
    assert not graph


def test_build_dependency_graph_no_dependencies(
    basic_pipeline: AnnotationPipeline,
) -> None:
    """Test dependency graph with annotators without dependencies."""
    annotator1 = DummyAnnotator(attributes=[make_attr("attr1")])
    annotator1.pipeline = basic_pipeline
    annotator2 = DummyAnnotator(attributes=[make_attr("attr2")])
    annotator2.pipeline = basic_pipeline

    basic_pipeline.add_annotator(annotator1)
    basic_pipeline.add_annotator(annotator2)

    graph = _build_dependency_graph(basic_pipeline)

    assert len(graph) == 2
    assert all(len(deps) == 0 for deps in graph.values())


def test_build_dependency_graph_with_dependencies(
    basic_pipeline: AnnotationPipeline,
) -> None:
    """Test dependency graph with dependencies between annotators."""
    attr1 = make_attr("attr1")
    annotator1 = DummyAnnotator(attributes=[attr1])
    annotator1.pipeline = basic_pipeline

    annotator2 = DummyAnnotator(
        attributes=[make_attr("attr2")],
        dependencies=("attr1",),
    )
    annotator2.pipeline = basic_pipeline

    basic_pipeline.add_annotator(annotator1)
    basic_pipeline.add_annotator(annotator2)

    graph = _build_dependency_graph(basic_pipeline)

    assert len(graph) == 2
    info1 = annotator1.get_info()
    info2 = annotator2.get_info()

    assert graph[info1] == []
    assert len(graph[info2]) == 1
    assert graph[info2][0] == (info1, attr1)


# Tests for _get_dependencies_for


def test_get_dependencies_for_no_deps(
    basic_pipeline: AnnotationPipeline,
) -> None:
    """Test getting dependencies for annotator without dependencies."""
    annotator = DummyAnnotator(attributes=[make_attr("attr1")])
    annotator.pipeline = basic_pipeline
    basic_pipeline.add_annotator(annotator)

    deps = _get_dependencies_for(annotator, basic_pipeline)

    assert not deps


def test_get_dependencies_for_with_deps(
    basic_pipeline: AnnotationPipeline,
) -> None:
    """Test getting dependencies for annotator with dependencies."""
    attr1 = make_attr("attr1")
    annotator1 = DummyAnnotator(attributes=[attr1])
    annotator1.pipeline = basic_pipeline

    annotator2 = DummyAnnotator(
        attributes=[make_attr("attr2")],
        dependencies=("attr1",),
    )
    annotator2.pipeline = basic_pipeline

    basic_pipeline.add_annotator(annotator1)
    basic_pipeline.add_annotator(annotator2)

    deps = _get_dependencies_for(annotator2, basic_pipeline)

    assert len(deps) == 1
    assert deps[0] == (annotator1.get_info(), attr1)


# Tests for _get_rerun_annotators


def test_get_rerun_annotators_no_new(
    basic_pipeline: AnnotationPipeline,
) -> None:
    """Test rerun annotators when nothing is new."""
    rerun = _get_rerun_annotators(basic_pipeline, [])
    assert rerun == set()


def test_get_rerun_annotators_with_internal_dependency(
    basic_pipeline: AnnotationPipeline,
) -> None:
    """Test rerun annotators with internal attribute dependency."""
    attr1 = make_attr("attr1", internal=True)
    annotator1 = DummyAnnotator(attributes=[attr1])
    annotator1.pipeline = basic_pipeline

    annotator2 = DummyAnnotator(
        attributes=[make_attr("attr2")],
        dependencies=("attr1",),
    )
    annotator2.pipeline = basic_pipeline

    basic_pipeline.add_annotator(annotator1)
    basic_pipeline.add_annotator(annotator2)

    info2 = annotator2.get_info()
    rerun = _get_rerun_annotators(basic_pipeline, [info2])

    # Should include annotator1 because attr1 is internal
    assert annotator1.get_info() in rerun


def test_get_rerun_annotators_downstream(
    basic_pipeline: AnnotationPipeline,
) -> None:
    """Test that downstream annotators are marked for rerun."""
    attr1 = make_attr("attr1")
    annotator1 = DummyAnnotator(attributes=[attr1])
    annotator1.pipeline = basic_pipeline

    annotator2 = DummyAnnotator(
        attributes=[make_attr("attr2")],
        dependencies=("attr1",),
    )
    annotator2.pipeline = basic_pipeline

    basic_pipeline.add_annotator(annotator1)
    basic_pipeline.add_annotator(annotator2)

    info1 = annotator1.get_info()
    rerun = _get_rerun_annotators(basic_pipeline, [info1])

    # annotator2 depends on annotator1, so it should be marked for rerun
    assert annotator2.get_info() in rerun


# Tests for _get_deleted_attributes


def test_get_deleted_attributes_no_changes(
    test_repo: GenomicResourceRepo,
) -> None:
    """Test deleted attributes when pipelines are identical."""
    pipeline1 = AnnotationPipeline(test_repo)
    annotator = DummyAnnotator(attributes=[make_attr("attr1")])
    annotator.pipeline = pipeline1
    pipeline1.add_annotator(annotator)

    pipeline2 = AnnotationPipeline(test_repo)
    annotator2 = DummyAnnotator(attributes=[make_attr("attr1")])
    annotator2.pipeline = pipeline2
    pipeline2.add_annotator(annotator2)

    deleted = _get_deleted_attributes(pipeline2, pipeline1)
    assert deleted == []


def test_get_deleted_attributes_removed_annotator(
    test_repo: GenomicResourceRepo,
) -> None:
    """Test deleted attributes when annotator is removed."""
    pipeline1 = AnnotationPipeline(test_repo)
    annotator = DummyAnnotator(attributes=[make_attr("attr1")])
    annotator.pipeline = pipeline1
    pipeline1.add_annotator(annotator)

    pipeline2 = AnnotationPipeline(test_repo)

    deleted = _get_deleted_attributes(pipeline2, pipeline1)
    assert "attr1" in deleted


def test_get_deleted_attributes_full_reannotation(
    test_repo: GenomicResourceRepo,
) -> None:
    """Test deleted attributes with full reannotation flag."""
    pipeline1 = AnnotationPipeline(test_repo)
    annotator = DummyAnnotator(attributes=[make_attr("attr1")])
    annotator.pipeline = pipeline1
    pipeline1.add_annotator(annotator)

    # Even with identical pipeline, full_reannotation returns all attrs
    pipeline2 = AnnotationPipeline(test_repo)
    annotator2 = DummyAnnotator(attributes=[make_attr("attr1")])
    annotator2.pipeline = pipeline2
    pipeline2.add_annotator(annotator2)

    deleted = _get_deleted_attributes(
        pipeline2, pipeline1, full_reannotation=True,
    )
    assert "attr1" in deleted


def test_get_deleted_attributes_internal_excluded(
    test_repo: GenomicResourceRepo,
) -> None:
    """Test that internal attributes are not included in deleted list."""
    pipeline1 = AnnotationPipeline(test_repo)
    annotator = DummyAnnotator(
        attributes=[
            make_attr("attr1", internal=True),
            make_attr("attr2", internal=False),
        ],
    )
    annotator.pipeline = pipeline1
    pipeline1.add_annotator(annotator)

    pipeline2 = AnnotationPipeline(test_repo)

    deleted = _get_deleted_attributes(pipeline2, pipeline1)
    assert "attr1" not in deleted
    assert "attr2" in deleted


# Tests for Annotator class


def test_annotator_get_info() -> None:
    """Test getting annotator info."""
    annotator = DummyAnnotator()

    info = annotator.get_info()
    assert info.annotator_id == "dummy"
    assert info.type == "dummy_annotator"
    assert not info.attributes


def test_annotator_open_close() -> None:
    """Test annotator open/close lifecycle."""
    annotator = DummyAnnotator()

    assert not annotator._is_open

    annotator.open()
    assert annotator._is_open

    annotator.close()
    assert not annotator._is_open


def test_annotator_resources_property() -> None:
    """Test annotator resources property."""
    mock_resource = Mock()
    info = AnnotatorInfo("test", [], {}, resources=[mock_resource])
    annotator = DummyAnnotator()
    annotator._info = info

    assert annotator.resources == [mock_resource]


def test_annotator_resource_ids_property() -> None:
    """Test annotator resource_ids property."""
    mock_resource = Mock()
    mock_resource.get_id.return_value = "test_id"
    info = AnnotatorInfo("test", [], {}, resources=[mock_resource])
    annotator = DummyAnnotator()
    annotator._info = info

    assert annotator.resource_ids == {"test_id"}


def test_annotator_attributes_property() -> None:
    """Test annotator attributes property."""
    attrs = [make_attr("attr1")]
    annotator = DummyAnnotator(attributes=attrs)

    assert annotator.attributes == attrs


def test_annotator_empty_result() -> None:
    """Test empty result generation."""
    attrs = [make_attr("attr1"), make_attr("attr2")]
    annotator = DummyAnnotator(attributes=attrs)

    result = annotator._empty_result()
    assert result == {"attr1": None, "attr2": None}


def test_annotator_batch_annotate_default() -> None:
    """Test default batch_annotate implementation."""
    annotator = DummyAnnotator(attributes=[make_attr("index")])
    annotator.open()

    annotatables = [Position("chr1", 1), Position("chr1", 2)]
    contexts: list[dict[str, Any]] = [{}, {}]

    results = list(annotator.batch_annotate(annotatables, contexts))

    assert len(results) == 2
    assert results[0]["index"] == 1
    assert results[1]["index"] == 2


# Tests for AnnotationPipeline class


def test_pipeline_init(test_repo: GenomicResourceRepo) -> None:
    """Test pipeline initialization."""
    pipeline = AnnotationPipeline(test_repo)

    assert pipeline.repository == test_repo
    assert not pipeline.annotators
    assert pipeline.preamble is None
    assert not pipeline.raw
    assert not pipeline._is_open


def test_pipeline_add_annotator(
    basic_pipeline: AnnotationPipeline,
) -> None:
    """Test adding annotator to pipeline."""
    annotator = DummyAnnotator()

    basic_pipeline.add_annotator(annotator)

    assert len(basic_pipeline.annotators) == 1
    assert basic_pipeline.annotators[0] == annotator


def test_pipeline_get_info(basic_pipeline: AnnotationPipeline) -> None:
    """Test getting pipeline info."""
    annotator = DummyAnnotator()
    basic_pipeline.add_annotator(annotator)

    infos = basic_pipeline.get_info()

    assert len(infos) == 1
    assert infos[0] == annotator.get_info()


def test_pipeline_get_attributes(
    basic_pipeline: AnnotationPipeline,
) -> None:
    """Test getting all attributes from pipeline."""
    attr1 = make_attr("attr1")
    attr2 = make_attr("attr2")

    annotator1 = DummyAnnotator(attributes=[attr1])
    annotator2 = DummyAnnotator(attributes=[attr2])

    basic_pipeline.add_annotator(annotator1)
    basic_pipeline.add_annotator(annotator2)

    attrs = basic_pipeline.get_attributes()

    assert len(attrs) == 2
    assert attr1 in attrs
    assert attr2 in attrs


def test_pipeline_get_attribute_info_found(
    basic_pipeline: AnnotationPipeline,
) -> None:
    """Test getting specific attribute info."""
    attr = make_attr("test_attr")
    annotator = DummyAnnotator(attributes=[attr])
    basic_pipeline.add_annotator(annotator)

    found_attr = basic_pipeline.get_attribute_info("test_attr")

    assert found_attr == attr


def test_pipeline_get_attribute_info_not_found(
    basic_pipeline: AnnotationPipeline,
) -> None:
    """Test getting non-existent attribute info."""
    found_attr = basic_pipeline.get_attribute_info("nonexistent")

    assert found_attr is None


def test_pipeline_annotate_auto_opens(
    basic_pipeline: AnnotationPipeline,
) -> None:
    """Test that annotate automatically opens pipeline."""
    annotator = DummyAnnotator(attributes=[make_attr("index")])
    basic_pipeline.add_annotator(annotator)

    assert not basic_pipeline._is_open

    basic_pipeline.annotate(Position("chr1", 1))

    assert basic_pipeline._is_open


def test_pipeline_annotate_with_context(
    basic_pipeline: AnnotationPipeline,
) -> None:
    """Test annotation with existing context."""
    annotator = DummyAnnotator(attributes=[make_attr("index")])
    basic_pipeline.add_annotator(annotator)
    basic_pipeline.open()

    context = {"existing": "value"}
    result = basic_pipeline.annotate(Position("chr1", 1), context)

    assert "existing" in result
    assert result["existing"] == "value"
    assert "index" in result


def test_pipeline_annotate_none() -> None:
    """Test annotating None annotatable."""
    repo = build_inmemory_test_repository({})
    pipeline = AnnotationPipeline(repo)
    annotator = DummyAnnotator()
    pipeline.add_annotator(annotator)

    result = pipeline.annotate(None)

    assert result == {}


def test_pipeline_batch_annotate(
    basic_pipeline: AnnotationPipeline,
) -> None:
    """Test batch annotation."""
    annotator = DummyAnnotator(attributes=[make_attr("index")])
    basic_pipeline.add_annotator(annotator)
    basic_pipeline.open()

    annotatables = [Position("chr1", 1), Position("chr1", 2)]

    results = basic_pipeline.batch_annotate(annotatables)

    assert len(results) == 2
    assert results[0]["index"] == 1
    assert results[1]["index"] == 2


def test_pipeline_close() -> None:
    """Test closing pipeline."""
    repo = build_inmemory_test_repository({})
    pipeline = AnnotationPipeline(repo)
    annotator = DummyAnnotator()
    pipeline.add_annotator(annotator)
    assert pipeline.repository == repo

    pipeline.open()
    assert pipeline._is_open
    assert annotator._is_open
    assert pipeline.repository == repo

    pipeline.close()
    assert not pipeline._is_open
    assert not annotator._is_open
    assert pipeline.repository == repo


def test_pipeline_context_manager(
    test_repo: GenomicResourceRepo,
) -> None:
    """Test using pipeline as context manager."""
    pipeline = AnnotationPipeline(test_repo)
    annotator = DummyAnnotator()
    pipeline.add_annotator(annotator)

    with pipeline as p:
        assert p == pipeline

    # After exiting, pipeline should be closed
    assert not pipeline._is_open


def test_pipeline_context_manager_with_exception(
    test_repo: GenomicResourceRepo,
) -> None:
    """Test context manager handles exceptions."""
    pipeline = AnnotationPipeline(test_repo)

    with pytest.raises(ValueError, match="test"), pipeline:
        raise ValueError("test")

    # Pipeline should still be closed
    assert not pipeline._is_open


#  Tests for ReannotationPipeline


def test_reannotation_pipeline_no_changes(
    test_repo: GenomicResourceRepo,
) -> None:
    """Test reannotation with identical pipelines."""
    pipeline1 = AnnotationPipeline(test_repo)
    annotator = DummyAnnotator(attributes=[make_attr("attr1")])
    annotator.pipeline = pipeline1
    pipeline1.add_annotator(annotator)

    pipeline2 = AnnotationPipeline(test_repo)
    annotator2 = DummyAnnotator(attributes=[make_attr("attr1")])
    annotator2.pipeline = pipeline2
    pipeline2.add_annotator(annotator2)

    reannot_pipeline = ReannotationPipeline(pipeline2, pipeline1)

    assert len(reannot_pipeline.annotators) == 0
    assert reannot_pipeline.deleted_attributes == []


def test_reannotation_pipeline_new_annotator(
    test_repo: GenomicResourceRepo,
) -> None:
    """Test reannotation with new annotator."""
    pipeline1 = AnnotationPipeline(test_repo)

    pipeline2 = AnnotationPipeline(test_repo)
    annotator = DummyAnnotator(attributes=[make_attr("attr1")])
    annotator.pipeline = pipeline2
    pipeline2.add_annotator(annotator)

    reannot_pipeline = ReannotationPipeline(pipeline2, pipeline1)

    assert len(reannot_pipeline.annotators) == 1
    assert annotator in reannot_pipeline.annotators


def test_reannotation_pipeline_removed_annotator(
    test_repo: GenomicResourceRepo,
) -> None:
    """Test reannotation with removed annotator."""
    pipeline1 = AnnotationPipeline(test_repo)
    annotator = DummyAnnotator(attributes=[make_attr("attr1")])
    annotator.pipeline = pipeline1
    pipeline1.add_annotator(annotator)

    pipeline2 = AnnotationPipeline(test_repo)

    reannot_pipeline = ReannotationPipeline(pipeline2, pipeline1)

    assert "attr1" in reannot_pipeline.deleted_attributes


# Tests for InputAnnotableAnnotatorDecorator


def test_input_annotatable_decorator_no_param() -> None:
    """Test decorator not applied without input_annotatable parameter."""
    annotator = DummyAnnotator()

    result = InputAnnotableAnnotatorDecorator.decorate(annotator)

    assert result == annotator
    assert not isinstance(result, InputAnnotableAnnotatorDecorator)


def test_input_annotatable_decorator_no_pipeline() -> None:
    """Test decorator raises error without pipeline."""
    annotator = DummyAnnotator()
    annotator._info.parameters._data["input_annotatable"] = "input_ann"

    with pytest.raises(ValueError, match="can only work within a pipeline"):
        InputAnnotableAnnotatorDecorator(annotator)


def test_input_annotatable_decorator_missing_attribute(
    test_repo: GenomicResourceRepo,
) -> None:
    """Test decorator raises error if attribute doesn't exist."""
    pipeline = AnnotationPipeline(test_repo)

    annotator = DummyAnnotator()
    annotator.pipeline = pipeline
    annotator._info.parameters._data["input_annotatable"] = "missing_attr"

    with pytest.raises(ValueError, match="has not been defined"):
        InputAnnotableAnnotatorDecorator(annotator)


# Tests for ValueTransformAnnotatorDecorator


def test_value_transform_decorator_no_transform() -> None:
    """Test decorator not applied without value_transform."""
    annotator = DummyAnnotator(attributes=[make_attr("attr1")])

    result = ValueTransformAnnotatorDecorator.decorate(annotator)

    assert result == annotator
    assert not isinstance(result, ValueTransformAnnotatorDecorator)


def test_value_transform_decorator_with_transform() -> None:
    """Test decorator applied with value_transform."""
    annotator = DummyAnnotator(
        attributes=[
            make_attr("attr1", value_transform="value * 2"),
        ],
    )

    result = ValueTransformAnnotatorDecorator.decorate(annotator)

    assert isinstance(result, ValueTransformAnnotatorDecorator)


def test_value_transform_decorator_invalid_transform() -> None:
    """Test decorator raises error for invalid transform syntax."""
    annotator = DummyAnnotator(
        attributes=[
            make_attr("attr1", value_transform="invalid syntax!!!"),
        ],
    )

    with pytest.raises(ValueError, match="sytactically invalid"):
        ValueTransformAnnotatorDecorator.decorate(annotator)


def test_value_transform_decorator_annotate() -> None:
    """Test decorator applies transformation."""

    class TestAnnotator(Annotator):
        """Annotator for testing value transformation."""

        def __init__(self) -> None:
            info = AnnotatorInfo(
                "test",
                attributes=[
                    make_attr("doubled", value_transform="value * 2"),
                    make_attr("normal"),
                ],
                parameters={},
            )
            super().__init__(None, info)

        def annotate(
            self,
            annotatable: Annotatable | None,  # noqa: ARG002
            context: dict[str, Any],  # noqa: ARG002
        ) -> dict[str, Any]:
            return {"doubled": 5, "normal": 10}

    annotator = TestAnnotator()
    decorator = ValueTransformAnnotatorDecorator.decorate(annotator)

    result = decorator.annotate(None, {})

    assert result["doubled"] == 10  # 5 * 2
    assert result["normal"] == 10  # unchanged
