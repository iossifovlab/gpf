
from typing import Any

from dae.annotation.annotatable import Annotatable
from dae.annotation.annotation_config import AnnotatorInfo, AttributeInfo
from dae.annotation.annotation_pipeline import (
    AnnotationPipeline,
    Annotator,
)


class HelloWorldAnnotator(Annotator):
    """Defines example annotator."""

    def __init__(self, pipeline: AnnotationPipeline, info: AnnotatorInfo):
        super().__init__(pipeline, info)

    def annotate(
        self, _annotatable: Annotatable | None, _context: dict[str, Any],
    ) -> dict[str, Any]:
        result = {}
        for attribute_config in self._info.attributes:
            assert attribute_config.source == "hi"
            result[attribute_config.name] = "hello world"
        return result


def build_annotator(pipeline: AnnotationPipeline,
                    info: AnnotatorInfo) -> Annotator:
    """Create an example hello world annotator."""
    if not info.attributes:
        info.attributes = [AttributeInfo("hi", "hi", False, {})]

    for attribute_info in info.attributes:
        if attribute_info.source != "hi":
            raise ValueError(f"The {info.type} does not provide the source "
                             f"{attribute_info.source}. The only source "
                             "provided is 'hi'")
        attribute_info.type = "str"
        attribute_info.description = \
            "The attribute 'hi' has as constant value of 'hello world.'"
    return HelloWorldAnnotator(pipeline, info)
