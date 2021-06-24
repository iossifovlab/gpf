from dae.configuration.gpf_config_parser import GPFConfigParser
from dae.annotation.tools.utils import AnnotatorFactory


class AnnotationConfigParser:
    @classmethod
    def load_annotation_config(cls, filename, override=None):
        raw_config = GPFConfigParser.load_config_raw(filename)
        annotator_type = raw_config["score_type"]
        annotator_class = AnnotatorFactory.name_to_class(annotator_type)
        schema = annotator_class.get_config_schema()
        config = GPFConfigParser.load_config(filename, schema)
        if override is not None:
            config = GPFConfigParser.modify_tuple(config, override)

        return config
