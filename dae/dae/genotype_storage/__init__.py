import logging
from typing import Callable, Dict, Any, List

from .genotype_storage import GenotypeStorage


logger = logging.getLogger(__file__)

_REGISTERED_GENOTYPE_STORAGE_FACTORIES: \
    Dict[str, Callable[[Dict[str, Any]], GenotypeStorage]] = {}
_EXTENTIONS_LOADED = False


def get_genotype_storage_factory(
        storage_type: str) -> Callable[[Dict[str, Any]], GenotypeStorage]:
    """Find and return a factory function for creation of a storage type."""
    if storage_type not in _REGISTERED_GENOTYPE_STORAGE_FACTORIES:
        raise ValueError(f"unsupported storage type: {storage_type}")
    return _REGISTERED_GENOTYPE_STORAGE_FACTORIES[storage_type]


def get_genotype_storage_types() -> List[str]:
    return list(_REGISTERED_GENOTYPE_STORAGE_FACTORIES.keys())


def register_genotype_storage_factory(
        storage_type: str,
        factory: Callable[[Dict[str, Any]], GenotypeStorage]) -> None:
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
        register_genotype_storage_factory(storage_type, factory)
    _EXTENTIONS_LOADED = True


_load_genotype_storage_factory_plugins()
