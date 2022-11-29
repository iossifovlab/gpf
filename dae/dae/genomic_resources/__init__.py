from typing import Dict, Callable
from importlib_metadata import entry_points

from .repository_factory import build_genomic_resource_repository
from .repository import GenomicResource
from .resource_implementation import GenomicResourceImplementation


_REGISTERED_RESOURCE_IMPLEMENTATIONS: \
    Dict[str, Callable[[GenomicResource], GenomicResourceImplementation]] = {}


__all__ = [
    "build_genomic_resource_repository", "GenomicResource",
    "get_resource_implementation_factory"
]


_IMPLEMENTATIONS_LOADED = False
_PLUGINS_LOADED = False


def get_resource_implementation_factory(
    implementation_type: str
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


def register_implementation(implementation_type, factory):
    _REGISTERED_RESOURCE_IMPLEMENTATIONS[implementation_type] = factory


def _load_implementations():
    # pylint: disable=global-statement
    global _IMPLEMENTATIONS_LOADED

    if _IMPLEMENTATIONS_LOADED:
        return

    discovered_implementations = entry_points(
        group="dae.genomic_resources.implementations"
    )

    for implementation_factory in discovered_implementations:
        implementation_type = implementation_factory.name
        factory = implementation_factory.load()
        register_implementation(implementation_type, factory)

    _IMPLEMENTATIONS_LOADED = True


def _load_plugins():
    # pylint: disable=global-statement
    global _PLUGINS_LOADED

    if _PLUGINS_LOADED:
        return

    # pylint: disable=import-outside-toplevel
    discovered_plugins = entry_points(group="dae.genomic_resources.plugins")
    for plugin in discovered_plugins:
        plugin.load()()
    _PLUGINS_LOADED = True


_load_plugins()
_load_implementations()
