from .import_tools import register_import_storage_factory

_EXTENTIONS_LOADED = False


def _load_import_storage_factory_plugins():
    # pylint: disable=global-statement
    global _EXTENTIONS_LOADED
    if _EXTENTIONS_LOADED:
        return
    # pylint: disable=import-outside-toplevel
    from importlib_metadata import entry_points
    discovered_entries = entry_points(group="dae.import_tools.storages")
    for entry in discovered_entries:
        storage_type = entry.name
        factory = entry.load()
        register_import_storage_factory(storage_type, factory)
    _EXTENTIONS_LOADED = True


_load_import_storage_factory_plugins()
