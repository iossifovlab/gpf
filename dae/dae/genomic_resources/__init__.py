from typing import Dict, Callable
from importlib_metadata import entry_points, EntryPoint

from .repository_factory import build_genomic_resource_repository
from .repository import GenomicResource
from .resource_implementation import GenomicResourceImplementation


_FOUND_RESOURCE_IMPLEMENTATIONS: Dict[str, EntryPoint] = {}


_REGISTERED_RESOURCE_IMPLEMENTATIONS: Dict[
    str, Callable[[GenomicResource], GenomicResourceImplementation]] = {}


__all__ = [
    "build_genomic_resource_repository", "GenomicResource",
    "get_resource_implementation_builder"
]


_IMPLEMENTATIONS_LOADED = False
_PLUGINS_LOADED = False


def get_resource_implementation_builder(
    resource_type: str
) -> Callable[[GenomicResource], GenomicResourceImplementation]:
    """
    Return an implementation builder for a certain resource type.

    If the builder is not registered, then it will search for an entry point
    in the found implementations list. If an entry point is found, it will be
    loaded and registered and returned.
    """
    if resource_type not in _REGISTERED_RESOURCE_IMPLEMENTATIONS:
        if resource_type not in _FOUND_RESOURCE_IMPLEMENTATIONS:
            raise ValueError(
                f"unsupported resource implementation type: {resource_type}"
            )
        entry_point = _FOUND_RESOURCE_IMPLEMENTATIONS[resource_type]
        loaded = entry_point.load()
        register_implementation(resource_type, loaded)

    return _REGISTERED_RESOURCE_IMPLEMENTATIONS[resource_type]


def register_implementation(
    resource_type: str,
    builder: Callable[[GenomicResource], GenomicResourceImplementation]
):
    """
    Register a resource type with a given builder function.

    The builder has to be a builder function which takes a genomic resource
    and returns a ready to use implementation.
    The type is the type of resource to which this builder will be mapped.
    This is usually the "type" field in the resource's config.
    """
    _REGISTERED_RESOURCE_IMPLEMENTATIONS[resource_type] = builder


def _find_implementations():
    """
    Find and record implementations specified in entry points.

    This will record all implementations specified in the
    setup.py of the project. The implementations are stored as entry points
    and will be loaded and registered later on demand to avoid cyclic imports.
    """
    # pylint: disable=global-statement
    global _IMPLEMENTATIONS_LOADED

    if _IMPLEMENTATIONS_LOADED:
        return

    discovered_implementations = entry_points(
        group="dae.genomic_resources.implementations"
    )

    for entry_point in discovered_implementations:
        _FOUND_RESOURCE_IMPLEMENTATIONS[entry_point.name] = entry_point

    _IMPLEMENTATIONS_LOADED = True


def _load_plugins():
    # pylint: disable=global-statement
    global _PLUGINS_LOADED

    if _PLUGINS_LOADED:
        return

    discovered_plugins = entry_points(group="dae.genomic_resources.plugins")
    for plugin in discovered_plugins:
        plugin.load()()
    _PLUGINS_LOADED = True


_load_plugins()
_find_implementations()
