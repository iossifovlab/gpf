"""Provides annotation pipeline class."""

from __future__ import annotations

import abc
import itertools
import logging
from collections.abc import Callable, Iterable, Sequence
from types import TracebackType
from typing import Any

from dae.annotation.annotatable import Annotatable
from dae.annotation.annotation_config import (
    AnnotationPreamble,
    AnnotatorInfo,
    AttributeInfo,
    RawPipelineConfig,
)
from dae.genomic_resources.genomic_context import (
    GenomicContext,
    PriorityGenomicContext,
    SimpleGenomicContext,
    get_genomic_context,
)
from dae.genomic_resources.reference_genome import (
    build_reference_genome_from_resource,
)
from dae.genomic_resources.repository import (
    GenomicResource,
    GenomicResourceRepo,
)

logger = logging.getLogger(__name__)
GC_GRR_KEY = "genomic_resources_repository"
GC_REFERENCE_GENOME_KEY = "reference_genome"
GC_GENE_MODELS_KEY = "gene_models"

_AnnotationDependencyGraph = dict[
    AnnotatorInfo, list[tuple[AnnotatorInfo, AttributeInfo]],
]


def _get_dependencies_for(
    info: AnnotatorInfo,
    dependency_graph: _AnnotationDependencyGraph,
) -> set[AnnotatorInfo]:
    """Get all dependencies for a given annotator."""
    result: set[AnnotatorInfo] = set()
    if info in dependency_graph:
        for annotator, attr in dependency_graph[info]:
            if attr.internal:
                result.add(annotator)
                dependencies = _get_dependencies_for(
                    annotator, dependency_graph)
                if dependencies:
                    result.add(*dependencies)
    return result


def _get_dependents_for(
    info: AnnotatorInfo,
    dependency_graph: _AnnotationDependencyGraph,
) -> set[AnnotatorInfo]:
    """Get all dependents for a given annotator."""
    result: set[AnnotatorInfo] = set()
    for dependent, dependencies in dependency_graph.items():
        if not dependencies:
            continue
        for dep_annotator, _ in dependencies:
            if dep_annotator == info:
                result.add(dependent)
                further = _get_dependents_for(dependent, dependency_graph)
                if further:
                    result.update(further)
    return result


def _build_dependency_graph(
    pipeline: AnnotationPipeline,
) -> _AnnotationDependencyGraph:
    """Make dependency graph for an annotation pipeline."""
    graph: _AnnotationDependencyGraph = {}
    for annotator in pipeline.annotators:
        annotator_info = annotator.get_info()
        if annotator_info not in graph:
            graph[annotator_info] = []
        for attr in annotator.used_context_attributes:
            attr_info = pipeline.get_attribute_info(attr)
            assert attr_info is not None
            upstream_annotator = \
                pipeline.get_annotator_by_attribute_info(attr_info)
            assert upstream_annotator is not None
            graph[annotator_info].append(
                (upstream_annotator.get_info(), attr_info),
            )
    return graph


def _get_rerun_annotators(
    pipeline: AnnotationPipeline,
    annotators_new: Iterable[AnnotatorInfo],
) -> set[AnnotatorInfo]:
    result: set[AnnotatorInfo] = set()
    dependency_graph = _build_dependency_graph(pipeline)
    for i in annotators_new:
        result.update(_get_dependencies_for(i, dependency_graph))
        result.update(_get_dependents_for(i, dependency_graph))

    logger.debug("RE-RUNNING ANNOTATORS - %s", result)
    return result


def get_deleted_attributes(
    infos_new: Iterable[AnnotatorInfo],
    infos_old: Iterable[AnnotatorInfo],
) -> list[str]:
    """Get a list of attributes that are deleted in the new annotation."""
    result: list[str] = []
    for deleted_info in [i for i in infos_old if i not in infos_new]:
        result.extend([attr.name for attr in deleted_info.attributes
                       if not attr.internal])
    return result


class Annotator(abc.ABC):
    """Annotator provides a set of attrubutes for a given Annotatable."""

    def __init__(self, pipeline: AnnotationPipeline | None,
                 info: AnnotatorInfo):
        self.pipeline = pipeline
        self._info = info
        self._is_open = False

    def get_info(self) -> AnnotatorInfo:
        return self._info

    @abc.abstractmethod
    def annotate(
        self, annotatable: Annotatable | None, context: dict[str, Any],
    ) -> dict[str, Any]:
        """Produce annotation attributes for an annotatable."""

    def batch_annotate(
        self, annotatables: Sequence[Annotatable | None],
        contexts: list[dict[str, Any]],
        batch_work_dir: str | None = None,  # noqa: ARG002
    ) -> Iterable[dict[str, Any]]:
        return itertools.starmap(
            self.annotate, zip(annotatables, contexts, strict=True),
        )

    def close(self) -> None:
        self._is_open = False

    def open(self) -> Annotator:
        self._is_open = True
        return self

    def is_open(self) -> bool:
        return self._is_open

    @property
    def resources(self) -> list[GenomicResource]:
        return self._info.resources

    @property
    def resource_ids(self) -> set[str]:
        return {resource.get_id() for resource in self._info.resources}

    @property
    def attributes(self) -> list[AttributeInfo]:
        return self._info.attributes

    @property
    def used_context_attributes(self) -> tuple[str, ...]:
        return ()

    def _empty_result(self) -> dict[str, Any]:
        return {attribute_info.name: None
                for attribute_info in self._info.attributes}


class AnnotationPipeline:
    """Provides annotation pipeline abstraction."""

    def __init__(self, repository: GenomicResourceRepo):
        self.repository: GenomicResourceRepo = repository
        self.annotators: list[Annotator] = []
        self.preamble: AnnotationPreamble | None = None
        self.raw: RawPipelineConfig = []
        self._is_open = False

        self._annotators_to_run: dict[AnnotatorInfo, bool] = {}

    def build_pipeline_genomic_context(self) -> GenomicContext:
        """Create a genomic context from the pipeline parameters."""
        registered_context = get_genomic_context()
        genome = None
        if self.preamble is not None:
            genome_res = self.preamble.input_reference_genome_res
            if genome_res is not None:
                genome = build_reference_genome_from_resource(genome_res)
        pipeline_context = SimpleGenomicContext({
            GC_GRR_KEY: self.repository,
            GC_REFERENCE_GENOME_KEY: genome,
        }, ("pipeline_context",))

        return PriorityGenomicContext([pipeline_context, registered_context])

    def get_info(self) -> list[AnnotatorInfo]:
        return [annotator.get_info() for annotator in self.annotators]

    def get_attributes(self) -> list[AttributeInfo]:
        return [attribute_info for annotator in self.annotators for
                attribute_info in annotator.attributes]

    def get_attribute_info(
            self, attribute_name: str) -> AttributeInfo | None:
        for annotator in self.annotators:
            for attribute_info in annotator.get_info().attributes:
                if attribute_info.name == attribute_name:
                    return attribute_info
        return None

    def get_resource_ids(self) -> set[str]:
        return {r_id for annotator in self.annotators
                for r_id in annotator.resource_ids}

    def get_annotator_by_attribute_info(
        self, attribute_info: AttributeInfo,
    ) -> Annotator | None:
        for annotator in self.annotators:
            if attribute_info in annotator.attributes:
                return annotator
        return None

    def add_annotator(self, annotator: Annotator) -> None:
        assert isinstance(annotator, Annotator)
        self.annotators.append(annotator)

    def annotate(
        self, annotatable: Annotatable | None,
        context: dict | None = None,
    ) -> dict:
        """Apply all annotators to an annotatable."""
        if not self._is_open:
            self.open()

        if context is None:
            context = {}

        for annotator in self.annotators:
            attributes = annotator.annotate(annotatable, context)
            context.update(attributes)

        return context

    def batch_annotate(
        self, annotatables: Sequence[Annotatable | None],
        contexts: list[dict] | None = None,
        batch_work_dir: str | None = None,
    ) -> list[dict]:
        """Apply all annotators to a list of annotatables."""
        if not self._is_open:
            self.open()

        if contexts is None:
            contexts = [{} for _ in annotatables]

        for annotator in self.annotators:
            attributes_list = annotator.batch_annotate(
                annotatables, contexts,
                batch_work_dir=batch_work_dir,
            )
            for context, attributes in zip(
                contexts, attributes_list, strict=True,
            ):
                context.update(attributes)

        return contexts

    def open(self) -> AnnotationPipeline:
        """Open all annotators in the pipeline and mark it as open."""
        if self._is_open:
            logger.warning("annotation pipeline is already open")
            return self

        assert not self._is_open
        for annotator in self.annotators:
            annotator.open()
        self._is_open = True
        return self

    def close(self) -> None:
        """Close the annotation pipeline."""
        for annotator in self.annotators:
            try:
                annotator.close()
            except Exception:  # pylint: disable=broad-except
                logger.exception(
                    "exception while closing annotator %s",
                    annotator.get_info())
        self._is_open = False

    def print(self) -> None:
        """Print the annotation pipeline."""
        print("NEW ATTRIBUTES -")
        for anno in self.annotators:
            for attr in anno.attributes:
                print("    +", attr.name)

    def __enter__(self) -> AnnotationPipeline:
        return self

    def __exit__(
            self,
            exc_type: type[BaseException] | None,
            exc_value: BaseException | None,
            exc_tb: TracebackType | None) -> bool:
        if exc_type is not None:
            logger.error(
                "exception during annotation: %s, %s, %s",
                exc_type, exc_value, exc_tb)
        self.close()
        return exc_type is None


class ReannotationPipeline(AnnotationPipeline):
    """Special pipeline that handles reannotation of a previous pipeline."""

    def __init__(
        self,
        pipeline_new: AnnotationPipeline,
        pipeline_old: AnnotationPipeline,
    ):
        """Produce a reannotation pipeline between two annotation pipelines."""
        super().__init__(pipeline_new.repository)
        self.pipeline_new: AnnotationPipeline = pipeline_new
        self.pipeline_old: AnnotationPipeline = pipeline_old

        self.preamble = self.pipeline_new.preamble
        self.raw = self.pipeline_new.raw

        infos_new = pipeline_new.get_info()
        infos_old = pipeline_old.get_info()

        self.annotators_new: set[AnnotatorInfo] = {
            i for i in infos_new if i not in infos_old
        }

        logger.debug("REANNOTATION SUMMARY:")
        logger.debug("NEW ANNOTATORS - %s", self.annotators_new)

        self.annotators_rerun = _get_rerun_annotators(
            self.pipeline_new,
            self.annotators_new,
        )

        for annotator in self.pipeline_new.annotators:
            info = annotator.get_info()
            if info in self.annotators_new or info in self.annotators_rerun:
                self.annotators.append(annotator)

    def get_attributes(self) -> list[AttributeInfo]:
        return self.pipeline_new.get_attributes()


class AnnotatorDecorator(Annotator):
    """Defines annotator decorator base class."""

    def __init__(self, child: Annotator):
        super().__init__(child.pipeline, child.get_info())
        self.child = child

    def close(self) -> None:
        self.child.close()

    def open(self) -> Annotator:
        return self.child.open()

    def is_open(self) -> bool:
        return self.child.is_open()

    def __getattr__(self, name: str) -> Any:
        return getattr(self.child, name)


class InputAnnotableAnnotatorDecorator(AnnotatorDecorator):
    """Defines annotator decorator to use input annotatable if defined."""

    @staticmethod
    def decorate(child: Annotator) -> Annotator:
        if "input_annotatable" in child.get_info().parameters:
            return InputAnnotableAnnotatorDecorator(child)
        return child

    def __init__(self, child: Annotator):
        super().__init__(child)

        assert "input_annotatable" in self._info.parameters
        self.input_annotatable_name = \
            self._info.parameters["input_annotatable"]

        if not self.pipeline:
            raise ValueError(
                "InputAnnotableAnnotatorDecorator can only work "
                "within a pipeline")
        att_info = self.pipeline.get_attribute_info(
            self.input_annotatable_name)
        if att_info is None:
            available_attributes = \
                ",".join([f"'{att.name}' [{att.type}]"
                          for att in self.pipeline.get_attributes()])
            raise ValueError(f"The attribute '{self.input_annotatable_name}' "
                             "has not been defined before its use. The "
                             "available attributes are: "
                             f"{available_attributes}")
        if att_info.type != "annotatable":
            raise ValueError(f"The attribute '{self.input_annotatable_name}' "
                             "is expected to be of type annotatable.")
        self.child._info.documentation += (  # noqa: SLF001
            f"\n* **input_annotatable**: `{self.input_annotatable_name}`"
        )

    @property
    def used_context_attributes(self) -> tuple[str, ...]:
        return (*self.child.used_context_attributes,
                self.input_annotatable_name)

    def annotate(
        self, annotatable: Annotatable | None,  # noqa: ARG002
        context: dict[str, Any],
    ) -> dict[str, Any]:

        input_annotatable = context[self.input_annotatable_name]

        if input_annotatable is None or \
           isinstance(input_annotatable, Annotatable):
            return self.child.annotate(input_annotatable, context)
        raise ValueError(
            f"The object with a key {input_annotatable} in the "
            f"annotation context {context} is not an Annotatable.",
        )


class ValueTransformAnnotatorDecorator(AnnotatorDecorator):
    """Define value transformer annotator decorator."""

    @staticmethod
    def decorate(child: Annotator) -> Annotator:
        """Apply value transform decorator to an annotator."""
        value_transformers: dict[str, Callable[[Any], Any]] = {}
        for attribute_info in child.get_info().attributes:
            if "value_transform" in attribute_info.parameters:
                transform_str = attribute_info.parameters["value_transform"]
                try:
                    # pylint: disable=eval-used
                    transform = eval(  # noqa: S307
                        f"lambda value: {transform_str}",
                    )
                except Exception as error:
                    raise ValueError(
                        f"The value trasform |{transform_str}| is "
                        f"sytactically invalid.", error) from error
                value_transformers[attribute_info.name] = transform
                # pylint: disable=protected-access
                attribute_info._documentation = (  # noqa: SLF001
                    f"{attribute_info.documentation}\n\n"
                    f"**value_transform:** {transform_str}"
                )
        if value_transformers:
            return ValueTransformAnnotatorDecorator(child, value_transformers)
        return child

    def __init__(self, child: Annotator,
                 value_transformers: dict[str, Callable[[Any], Any]]):
        super().__init__(child)
        self.value_transformers = value_transformers

    def annotate(
        self, annotatable: Annotatable | None, context: dict[str, Any],
    ) -> dict[str, Any]:
        result = self.child.annotate(annotatable, context)
        return {k: (self.value_transformers[k](v)
                    if k in self.value_transformers else v)
                for k, v in result.items()}


class FullReannotationPipeline(ReannotationPipeline):
    """
    Special-case ReannotationPipeline.

    Completely removes all old attributes and runs every new annotator,
    without reusing anything.
    """

    def __init__(
        self,
        pipeline_new: AnnotationPipeline,
        pipeline_old: AnnotationPipeline,
    ):
        super().__init__(pipeline_new, pipeline_old)

        self.attributes_deleted: list[str] = []
        for deleted_info in pipeline_old.get_info():
            for attr in deleted_info.attributes:
                if not attr.internal:
                    self.attributes_deleted.append(attr.name)

        self.annotators_new: set[AnnotatorInfo] = set(pipeline_new.get_info())

        self.annotators_rerun: set[AnnotatorInfo] = set()

        self.annotators = self.pipeline_new.annotators

        logger.debug("REANNOTATION SUMMARY:")
        logger.debug("DELETED ATTRIBUTES - %s", self.attributes_deleted)
        logger.debug("NEW ANNOTATORS - %s", self.annotators_new)
        logger.debug("RE-RUNNING ANNOTATORS - %s", self.annotators_rerun)
