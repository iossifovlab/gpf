"""Provides base class for annotators."""
from __future__ import annotations

import abc
import os
from collections.abc import Sequence
from dataclasses import (
    dataclass,
    field,
)
from itertools import starmap
from pathlib import Path
from typing import Any, cast

from dae.annotation.annotatable import Annotatable
from dae.annotation.annotation_config import (
    AnnotatorInfo,
    AttributeInfo,
)
from dae.annotation.annotation_pipeline import AnnotationPipeline, Annotator


@dataclass
class AttributeDesc:
    """Holds default attribute configuration for annotators."""

    name: str
    type: str
    description: str
    default: bool = True
    internal: bool = False
    params: dict[str, Any] = field(default_factory=dict)


class AnnotatorBase(Annotator):
    """Base implementation of the `Annotator` class."""

    def __init__(
        self, pipeline: AnnotationPipeline | None,
        info: AnnotatorInfo,
        attribute_descriptions: dict[str, tuple[str, str] | AttributeDesc],
    ):
        self.attribute_descriptions = {}
        for name, attr_desc in attribute_descriptions.items():
            if isinstance(attr_desc, tuple):
                self.attribute_descriptions[name] = AttributeDesc(
                    name=name,
                    type=attr_desc[0],
                    description=attr_desc[1],
                )
            elif isinstance(attr_desc, AttributeDesc):
                self.attribute_descriptions[name] = attr_desc
            else:
                raise TypeError(
                    f"Invalid attribute description for source '{name}'"
                    f" in annotator {info.type}")
        if not info.attributes:
            for attr_desc in self.attribute_descriptions.values():
                if attr_desc.default:
                    attr = AttributeInfo(
                        name=attr_desc.name,
                        source=attr_desc.name,
                        internal=attr_desc.internal,
                        parameters={},
                        _type=attr_desc.type,
                        description=attr_desc.description,
                    )
                    info.attributes.append(attr)

        for attribute_config in info.attributes:
            if attribute_config.source not in attribute_descriptions:
                raise ValueError(
                    f"The attribute source '{attribute_config.source}'"
                    " is not supported for the annotator"
                    f" {info.type}")
            attr_desc = self.attribute_descriptions[attribute_config.source]
            attribute_config.type = attr_desc.type
            attribute_config.description = attr_desc.description
            if attribute_config.internal is None:
                attribute_config.internal = attr_desc.internal

        self.work_dir: Path = cast(Path, info.parameters.get("work_dir"))
        super().__init__(pipeline, info)

    def open(self) -> Annotator:
        super().open()
        if self.work_dir is not None:
            os.makedirs(self.work_dir, exist_ok=True)
        return self

    @abc.abstractmethod
    def _do_annotate(self, annotatable: Annotatable, context: dict[str, Any]) \
            -> dict[str, Any]:
        """Annotate the annotatable.

        Internal abstract method used for annotation. It should produce
        all source attributes defined for annotator.
        """

    def annotate(
        self, annotatable: Annotatable | None, context: dict[str, Any],
    ) -> dict[str, Any]:
        if annotatable is None:
            return self._empty_result()
        source_values = self._do_annotate(annotatable, context)
        return {
            attribute_config.name: source_values[attribute_config.source]
            for attribute_config in self._info.attributes
        }

    def _do_batch_annotate(
        self,
        annotatables: Sequence[Annotatable | None],
        contexts: list[dict[str, Any]],
        batch_work_dir: str | None = None,  # noqa: ARG002
    ) -> list[dict[str, Any]]:
        """
        Annotate a batch of annotatables.

        Internal abstract method used for batch annotation.
        """
        return list(starmap(
            self._do_annotate, zip(annotatables, contexts, strict=True),
        ))

    def batch_annotate(
        self,
        annotatables: Sequence[Annotatable | None],
        contexts: list[dict[str, Any]],
        batch_work_dir: str | None = None,
    ) -> list[dict[str, Any]]:
        inner_output = self._do_batch_annotate(
            annotatables, contexts, batch_work_dir=batch_work_dir,
        )
        return [{
            attr.name: result[attr.source]
            for attr in self._info.attributes
        } for result in inner_output]
