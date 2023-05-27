"""Provides annotation pipeline class."""

from __future__ import annotations
import abc
from dataclasses import dataclass, field

import logging

from typing import Any, Callable, Optional

from dae.genomic_resources.repository import GenomicResource
from dae.genomic_resources.repository import GenomicResourceRepo

from dae.annotation.annotatable import Annotatable

logger = logging.getLogger(__name__)


@dataclass
class AttributeInfo:
    name: str
    source: str
    internal: bool
    parameters: dict[str, Any]
    type: str = "str"           # str, int, float, or object
    description: str = ""       # interpreted as md
    documentation: Optional[str] = None


@dataclass
class AnnotatorInfo:
    type: str
    attributes: list[AttributeInfo]
    parameters: dict[str, Any]
    resources: list[GenomicResource] = field(default_factory=list)


class Annotator(abc.ABC):
    """Annotator provides a set of attrubutes for a given Annotatable."""

    def __init__(self, pipeline: AnnotationPipeline, info: AnnotatorInfo):
        self.pipeline = pipeline
        self._info = info
        self._is_open = False

    def get_info(self) -> AnnotatorInfo:
        return self._info

    @abc.abstractmethod
    def annotate(self, annotatable: Annotatable, context: dict[str, Any]) \
            -> dict[str, Any]:
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

        # TODO: Decide where context should be cleaned up
        for annotator in self.annotators:
            for attr in annotator.get_info().attributes:
                if attr.internal:
                    del context[attr.name]

        return context

    def open(self) -> AnnotationPipeline:
        assert not self._is_open
        for annotator in self.annotators:
            annotator.open()
        self._is_open = True
        return self

    def close(self):
        for annotator in self.annotators:
            try:
                annotator.close()
            except Exception:  # pylint: disable=broad-except
                logger.error(
                    "exception while closing annotator %s",
                    annotator._info, exc_info=True)
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

        att_info = self.pipeline.get_attribute_info(
            self.input_annotatable_name)
        if att_info is None:
            raise Exception(f"The attribute {self.input_annotatable_name} "
                            "has not been defined before its use in "
                            f"{self._info}")
        if att_info.type != "object":
            raise Exception(f"The attribute {self.input_annotatable_name} "
                            "is expected to be of type object in "
                            f"{self._info}")

    def annotate(self, _: Annotatable, context: dict[str, Any]) \
            -> dict[str, Any]:

        input_annotatable = context[self.input_annotatable_name]

        if input_annotatable is None or \
           isinstance(input_annotatable, Annotatable):
            return self.child.annotate(input_annotatable, context)
        raise ValueError(
            f"The object with a key {input_annotatable} in the "
            f"annotation context {context} is not an Annotabable."
        )


class ValueTransormAnnotatorDecorator(AnnotatorDecorator):
    @staticmethod
    def decorate(child: Annotator) -> Annotator:
        value_transformers: dict[str, Callable[[Any], Any]] = {}
        for attribute_config in child.get_info().attributes:
            if "value_transform" in attribute_config.parameters:
                transform_str = attribute_config.parameters["value_transform"]
                try:
                    transform = eval("lambda value: " + transform_str)
                except Exception as e:
                    raise Exception(f"The value trasform |{transform_str}| is "
                                    "sytactically invalid.", e)
                value_transformers[attribute_config.name] = transform
        if value_transformers:
            return ValueTransormAnnotatorDecorator(child, value_transformers)
        return child

    def __init__(self, child: Annotator,
                 value_transformers: dict[str, Callable[[Any], Any]]):
        super().__init__(child)
        self.value_transformers = value_transformers

    def annotate(self, annotatable: Annotatable, context: dict[str, Any]) \
            -> dict[str, Any]:
        r = self.child.annotate(annotatable, context)
        return {k: (self.value_transformers[k](v)
                    if k in self.value_transformers else v)
                for k, v in r.items()}
