from dae.configuration.gpf_config_parser import GPFConfigParser
from dae.genomic_resources.utils import resource_type_to_class


class ResourcesConfigParser:
    @classmethod
    def load_resource_config(cls, filename, override=None):
        raw_config = GPFConfigParser.load_config_raw(filename)
        resource_type = raw_config["resource_type"]
        resource_class = resource_type_to_class(resource_type)
        schema = resource_class.get_config_schema()

        config = GPFConfigParser.load_config(filename, schema)
        if override is not None:
            config = GPFConfigParser.modify_tuple(config, override)

        return config

    @classmethod
    def load_resource_config_from_stream(cls, stream):
        file_contents = ""
        for chunk_raw in stream:
            file_contents += chunk_raw.decode("ascii")
        parsed_config = GPFConfigParser.interpolate_contents(
            file_contents, ".yaml"
        )
        resource_type = parsed_config["resource_type"]
        resource_class = resource_type_to_class(resource_type)
        schema = resource_class.get_config_schema()

        return GPFConfigParser.process_config(parsed_config, schema)
