import logging
from typing import Callable, Dict, Any, List

from .genotype_storage import GenotypeStorage


logger = logging.getLogger(__file__)

_REGISTERED_GENOTYPE_STORAGE_FACTORIES: \
    Dict[str, Callable[[Dict[str, Any]], GenotypeStorage]] = {}
_EXTENTIONS_LOADED = False


def get_genotype_storage_factory(
        storage_type: str) -> Callable[[Dict[str, Any]], GenotypeStorage]:
    """Find and return a factory function for creation of a storage type.

    If the specified storage type is not found, this function raises
    `ValueError` exception.

    :return: the genotype storage factory for the specified storage type.
    :raises ValueError: when can't find a genotype storage factory for the
        specified storage type.
    """
    _load_genotype_storage_factory_plugins()
    if storage_type not in _REGISTERED_GENOTYPE_STORAGE_FACTORIES:
        raise ValueError(f"unsupported storage type: {storage_type}")
    return _REGISTERED_GENOTYPE_STORAGE_FACTORIES[storage_type]


def get_genotype_storage_types() -> List[str]:
    """Return the list of all registered genotype storage factory types."""
    _load_genotype_storage_factory_plugins()
    return list(_REGISTERED_GENOTYPE_STORAGE_FACTORIES.keys())


def register_genotype_storage_factory(
        storage_type: str,
        factory: Callable[[Dict[str, Any]], GenotypeStorage]) -> None:
    """Register additional genotype storage factory.

    By default all genotype storage factories should be registered at
    `[dae.genotype_storage.factories]` extenstion point. All registered
    factories are loaded automatically. This function should be used if you
    want to bypass extension point mechanism and register addition genotype
    storage factory programatically.
    """
    _load_genotype_storage_factory_plugins()
    if storage_type in _REGISTERED_GENOTYPE_STORAGE_FACTORIES:
        logger.warning("overwriting genotype storage type: %s", storage_type)
    _REGISTERED_GENOTYPE_STORAGE_FACTORIES[storage_type] = factory


def _load_genotype_storage_factory_plugins():
    # pylint: disable=global-statement
    global _EXTENTIONS_LOADED
    if _EXTENTIONS_LOADED:
        return
    # pylint: disable=import-outside-toplevel
    from importlib_metadata import entry_points
    discovered_entries = entry_points(group="dae.genotype_storage.factories")
    for entry in discovered_entries:
        storage_type = entry.name
        factory = entry.load()
        if storage_type in _REGISTERED_GENOTYPE_STORAGE_FACTORIES:
            logger.warning(
                "overwriting genotype storage type: %s", storage_type)
        if storage_type != factory.get_storage_type():
            raise ValueError("missmatch genotype storage types")

        _REGISTERED_GENOTYPE_STORAGE_FACTORIES[storage_type] = factory
    _EXTENTIONS_LOADED = True
