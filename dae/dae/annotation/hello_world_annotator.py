
from typing import Any
from dae.annotation.annotatable import Annotatable
from dae.annotation.annotation_pipeline import AnnotationPipeline
from dae.annotation.annotator_base import Annotator, parse_raw_attributes
from dae.annotation.annotator_base import AnnotatorInfo


class HelloWorldAnnotator(Annotator):
    def __init__(self, config: AnnotatorInfo):
        super.__init__(config)
    
    def get_info(self) -> AnnotatorInfo:
        return self.config

    def annotate(self, annotatable: Annotatable,
                 context: dict[str, Any]) -> dict[str, Any]:
        r = {}
        for attribute_config in self.config.attributes:
            assert attribute_config.source = "hi"
            r[attribute_config.destination] = "hello world"


    

def build_annotator(pipeline: AnnotationPipeline, 
                    raw_config: dict[str, Any]) -> Annotator:
    
    raw_attributes = raw_config.get("attributes", ["hi"])
    attributes = parse_raw_attributes(raw_attributes)
    
    parameters = {k: v for k, v in raw_config.items() if k != "attributes"}
    annotator_info = AnnotatorInfo("hello world", parameters, [], attributes)
    
    return HelloWorldAnnotator(annotator_info)