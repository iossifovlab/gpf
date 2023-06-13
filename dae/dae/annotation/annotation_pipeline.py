"""Provides annotation pipeline class."""

from __future__ import annotations
import abc
from collections.abc import Mapping
from dataclasses import dataclass, field

import logging

from typing import Any, Callable, Optional

from dae.genomic_resources.repository import GenomicResource
from dae.genomic_resources.repository import GenomicResourceRepo

from dae.annotation.annotatable import Annotatable

logger = logging.getLogger(__name__)


@dataclass(init=False)
class AttributeInfo:
    """Defines annotation attribute configuration."""

    def __init__(self, name: str, source: str, internal: bool,
                 parameters: ParamsUsageMonitor | dict[str, Any],
                 _type: str = "str", description: str = "",
                 documentation: Optional[str] = None):
        self.name = name
        self.source = source
        self.internal = internal
        if isinstance(parameters, ParamsUsageMonitor):
            self.parameters = parameters
        else:
            self.parameters = ParamsUsageMonitor(parameters)
        self.type = _type
        self.description = description
        self._documentation = documentation

    name: str
    source: str
    internal: bool
    parameters: ParamsUsageMonitor
    type: str = "str"           # str, int, float, or object
    description: str = ""       # interpreted as md
    _documentation: Optional[str] = None

    @property
    def documentation(self):
        if self._documentation is None:
            return self.description
        return self._documentation


@dataclass(init=False)
class AnnotatorInfo:
    """Defines annotator configuration."""

    def __init__(self, _type: str, attributes: list[AttributeInfo],
                 parameters: ParamsUsageMonitor | dict[str, Any],
                 documentation: str = "",
                 resources: Optional[list[GenomicResource]] = None):
        self.type = _type
        self.attributes = attributes
        self.documentation = documentation
        if isinstance(parameters, ParamsUsageMonitor):
            self.parameters = parameters
        else:
            self.parameters = ParamsUsageMonitor(parameters)
        if resources is None:
            self.resources = []
        else:
            self.resources = resources

    type: str
    attributes: list[AttributeInfo]
    parameters: ParamsUsageMonitor
    documentation: str = ""
    resources: list[GenomicResource] = field(default_factory=list)


class Annotator(abc.ABC):
    """Annotator provides a set of attrubutes for a given Annotatable."""

    def __init__(self, pipeline: Optional[AnnotationPipeline],
                 info: AnnotatorInfo):
        self.pipeline = pipeline
        self._info = info
        self._is_open = False

    def get_info(self) -> AnnotatorInfo:
        return self._info

    @abc.abstractmethod
    def annotate(
        self, annotatable: Optional[Annotatable], context: dict[str, Any]
    ) -> dict[str, Any]:
        """Produce annotation attributes for an annotatable."""

    def close(self):
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

    def _empty_result(self) -> dict[str, Any]:
        return {attribute_info.name: None
                for attribute_info in self._info.attributes}


class AnnotationPipeline:
    """Provides annotation pipeline abstraction."""

    def __init__(
            self, repository: GenomicResourceRepo):

        self.repository: GenomicResourceRepo = repository
        self.annotators: list[Annotator] = []
        self._is_open = False

    def get_info(self) -> list[AnnotatorInfo]:
        return [annotator.get_info() for annotator in self.annotators]

    def get_attributes(self) -> list[AttributeInfo]:
        return [attribute_info for annotator in self.annotators for
                attribute_info in annotator.attributes]

    def get_attribute_info(self, attribute_name) -> Optional[AttributeInfo]:
        for annotator in self.annotators:
            for attribute_info in annotator.get_info().attributes:
                if attribute_info.name == attribute_name:
                    return attribute_info
        return None

    def get_resource_ids(self) -> set[str]:
        return {r_id for annotator in self.annotators
                for r_id in annotator.resource_ids}

    def add_annotator(self, annotator: Annotator) -> None:
        assert isinstance(annotator, Annotator)
        self.annotators.append(annotator)

    def annotate(self, annotatable: Annotatable) -> dict:
        """Apply all annotators to an annotatable."""
        if not self._is_open:
            self.open()

        context: dict = {}
        for annotator in self.annotators:
            attributes = annotator.annotate(annotatable, context)
            context.update(attributes)

        return context

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

    def close(self):
        """Close the annotation pipeline."""
        for annotator in self.annotators:
            try:
                annotator.close()
            except Exception:  # pylint: disable=broad-except
                logger.error(
                    "exception while closing annotator %s",
                    annotator.get_info(), exc_info=True)
        self._is_open = False

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, exc_tb):
        if exc_type is not None:
            logger.error(
                "exception during annotation: %s, %s, %s",
                exc_type, exc_value, exc_tb, exc_info=True)
        self.close()


class AnnotatorDecorator(Annotator):
    """Defines annotator decorator base class."""

    def __init__(self, child: Annotator):
        super().__init__(child.pipeline, child.get_info())
        self.child = child

    def close(self):
        self.child.close()

    def open(self) -> Annotator:
        return self.child.open()

    def is_open(self) -> bool:
        return self.child.is_open()


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
        if att_info.type != "object":
            raise ValueError(f"The attribute '{self.input_annotatable_name}' "
                             "is expected to be of type object.")
        self.child._info.documentation += \
            f"\n*input_annotatable*: {self.input_annotatable_name}"

    def annotate(
        self, _: Optional[Annotatable], context: dict[str, Any]
    ) -> dict[str, Any]:

        input_annotatable = context[self.input_annotatable_name]

        if input_annotatable is None or \
           isinstance(input_annotatable, Annotatable):
            return self.child.annotate(input_annotatable, context)
        raise ValueError(
            f"The object with a key {input_annotatable} in the "
            f"annotation context {context} is not an Annotabable."
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
                    transform = eval(f"lambda value: { transform_str }")
                except Exception as error:
                    raise ValueError(
                        f"The value trasform |{transform_str}| is "
                        f"sytactically invalid.", error) from error
                value_transformers[attribute_info.name] = transform
                # pylint: disable=protected-access
                attribute_info._documentation = \
                    f"{attribute_info.documentation}\n\n" \
                    f"**value_transform:** {transform_str}"
        if value_transformers:
            return ValueTransformAnnotatorDecorator(child, value_transformers)
        return child

    def __init__(self, child: Annotator,
                 value_transformers: dict[str, Callable[[Any], Any]]):
        super().__init__(child)
        self.value_transformers = value_transformers

    def annotate(
        self, annotatable: Optional[Annotatable], context: dict[str, Any]
    ) -> dict[str, Any]:
        result = self.child.annotate(annotatable, context)
        return {k: (self.value_transformers[k](v)
                    if k in self.value_transformers else v)
                for k, v in result.items()}


class ParamsUsageMonitor(Mapping):
    """Class to monitor usage of annotator parameters."""

    def __init__(self, data: dict[str, Any]):
        self._data = data
        self._used_keys: set[str] = set([])

    def __getitem__(self, key: str):
        self._used_keys.add(key)
        return self._data[key]

    def __len__(self):
        return len(self._data)

    def __iter__(self):
        raise ValueError("Should not iterate a parameter dictionary.")

    def __repr__(self):
        return self._data.__repr__()

    def __eq__(self, other):
        if not isinstance(other, ParamsUsageMonitor):
            return False
        return self._data == other._data

    def get_used_keys(self) -> set[str]:
        return self._used_keys

    def get_unused_keys(self) -> set[str]:
        return set(self._data.keys()) - self._used_keys
