from importlib import import_module


def aggregator_name_to_class(aggregator_name):
    module = import_module("dae.genomic_resources.aggregators")
    clazz = getattr(module, aggregator_name)
    return clazz


def resource_type_to_class(resource_type):
    splitted = resource_type.split(".")
    module_path = ".".join(splitted[:-1])
    class_name = splitted[-1]
    module = import_module(f"dae.genomic_resources.{module_path}")
    clazz = getattr(module, class_name)
    return clazz
