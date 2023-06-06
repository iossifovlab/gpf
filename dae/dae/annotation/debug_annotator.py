
from typing import Any
from .annotatable import Annotatable
from .annotation_pipeline import AnnotationPipeline, AttributeInfo
from .annotation_pipeline import Annotator
from .annotation_pipeline import AnnotatorInfo


class HelloWorldAnnotator(Annotator):
    def __init__(self, pipeline: AnnotationPipeline, info: AnnotatorInfo):
        super().__init__(pipeline, info)

    def annotate(self, _annotatable: Annotatable, _context: dict[str, Any]) \
            -> dict[str, Any]:
        r = {}
        for attribute_config in self._info.attributes:
            assert attribute_config.source == "hi"
            r[attribute_config.name] = "hello world"
        return r


def build_annotator(pipeline: AnnotationPipeline,
                    info: AnnotatorInfo) -> Annotator:

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
