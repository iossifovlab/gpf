import logging
import time
from collections.abc import Callable, Iterable
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from typing import Any, cast

from dae.genotype_storage.genotype_storage import GenotypeStorage
from dae.query_variants.query_runners import QueryResult
from dae.variants.family_variant import FamilyAllele, FamilyVariant
from dae.variants.variant import SummaryVariant

logger = logging.getLogger(__name__)


_REGISTERED_GENOTYPE_STORAGE_FACTORIES: \
    dict[str, Callable[[dict[str, Any]], GenotypeStorage]] = {}
_EXTENTIONS_LOADED = False


def get_genotype_storage_factory(
        storage_type: str) -> Callable[[dict[str, Any]], GenotypeStorage]:
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


def get_genotype_storage_types() -> list[str]:
    """Return the list of all registered genotype storage factory types."""
    _load_genotype_storage_factory_plugins()
    return list(_REGISTERED_GENOTYPE_STORAGE_FACTORIES.keys())


def register_genotype_storage_factory(
        storage_type: str,
        factory: Callable[[dict[str, Any]], GenotypeStorage]) -> None:
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


def _load_genotype_storage_factory_plugins() -> None:
    # pylint: disable=global-statement
    global _EXTENTIONS_LOADED

    if _EXTENTIONS_LOADED:
        return
    # pylint: disable=import-outside-toplevel
    from importlib.metadata import entry_points
    discovered_entries = entry_points(group="dae.genotype_storage.factories")

    for entry in discovered_entries:
        storage_type = entry.name
        factory = entry.load()
        if storage_type in _REGISTERED_GENOTYPE_STORAGE_FACTORIES:
            logger.warning(
                "overwriting genotype storage type: %s", storage_type)
        if hasattr(factory, "get_storage_types") and \
                storage_type not in factory.get_storage_types():
            raise ValueError("missmatch genotype storage types")

        _REGISTERED_GENOTYPE_STORAGE_FACTORIES[storage_type] = factory
    _EXTENTIONS_LOADED = True


class GenotypeStorageRegistry:
    """Registry for genotype storages.

    This class could accept genotype storages config from a GPF instance
    configuration and instantiate and register all genotype storages defined
    in this configuration. To do this, one could use
    :meth:`GenotypeStorageRegistry.register_storages_configs`.

    To create and register single genotype storage using its configuration
    you can use :meth:`GenotypeStorageRegistry.register_storage_config`.

    When you have already created an instance of genotype storage, you can use
    :meth:`GenotypeStorageRegistry.register_genotype_storage` to register
    it.
    """

    def __init__(self) -> None:
        self._genotype_storages: dict[str, GenotypeStorage] = {}
        self._default_genotype_storage: GenotypeStorage | None = None
        self.executor = ThreadPoolExecutor()

    def register_storage_config(
            self, storage_config: dict[str, Any]) -> GenotypeStorage:
        """Create a genotype storage using storage config and registers it."""
        storage_type = storage_config["storage_type"]
        storage_factory = get_genotype_storage_factory(storage_type)

        genotype_storage = storage_factory(storage_config)
        return self.register_genotype_storage(genotype_storage)

    def register_genotype_storage(
            self, storage: GenotypeStorage) -> GenotypeStorage:
        """Register a genotype storage instance."""
        if not isinstance(storage, GenotypeStorage):
            raise TypeError(
                f"trying to register object of type <{type(storage)}>"
                f" as genotype storage.")
        storage_id = storage.storage_id
        self._genotype_storages[storage_id] = storage
        return storage

    def register_default_storage(
            self, genotype_storage: GenotypeStorage) -> None:
        """Register a genotype storage and make it the default storage."""
        self.register_genotype_storage(genotype_storage)
        self._default_genotype_storage = genotype_storage

    def get_default_genotype_storage(self) -> GenotypeStorage:
        """Return the default genotype storage if one is defined.

        Otherwise, return None.
        """
        if self._default_genotype_storage is None:
            raise ValueError("default genotype storage not set")
        return self._default_genotype_storage

    def get_genotype_storage(self, storage_id: str) -> GenotypeStorage:
        """Return genotype storage with specified storage_id.

        If the method can not find storage with the specified ID, it will raise
        ValueError exception.
        """
        if storage_id is None:
            return self.get_default_genotype_storage()
        if storage_id not in self._genotype_storages:
            raise ValueError(f"unknown storage id: <{storage_id}>")
        return self._genotype_storages[storage_id]

    def get_all_genotype_storage_ids(self) -> list[str]:
        """Return list of all registered genotype storage IDs."""
        return list(self._genotype_storages.keys())

    def get_all_genotype_storages(self) -> list[GenotypeStorage]:
        """Return list of registered genotype storages."""
        return list(self._genotype_storages.values())

    def register_storages_configs(
            self, genotype_storages_config: dict[str, Any]) -> None:
        """Create and register all genotype storages defined in config.

        When defining a GPF instance, we specify a `genotype_storage` section
        in the configuration. If you pass this whole configuration section
        to this method, it will create and register all genotype storages
        defined in that configuration section.
        """
        for storage_config in genotype_storages_config["storages"]:
            self.register_storage_config(storage_config)
        default_storage_id = genotype_storages_config.get("default")
        if default_storage_id is not None:
            storage = self.get_genotype_storage(default_storage_id)
            self.register_default_storage(storage)

    def shutdown(self) -> None:
        for storage_id, storage in self._genotype_storages.items():
            logger.info("shutting down genotype storage %s", storage_id)
            storage.shutdown()

    def find_storage(self, study_id: str) -> GenotypeStorage:
        for storage in self._genotype_storages.values():
            if study_id not in storage.loaded_variants:
                continue
            return storage
        raise ValueError(f"{study_id} not found in registry!")

    def query_variants(
        self, study_ids: list[str], kwargs: dict[str, Any],
        max_variants_count: int | None = 10000,
    ) -> Iterable[FamilyVariant]:
        runners = []
        for study_id in study_ids:
            storage = self.find_storage(study_id)
            runner = storage.create_runner(study_id, kwargs)
            if runner is not None:
                runners.append(runner)

        summary_variant_ids = kwargs.pop("summaryVariantIds", None)

        if summary_variant_ids is None:
            # pylint: disable=unused-argument
            def filter_allele(
                allele: FamilyAllele,  # noqa: ARG001
            ) -> bool:
                return True

        elif len(summary_variant_ids) > 0:
            summary_variant_ids = set(summary_variant_ids)

            def filter_allele(allele: FamilyAllele) -> bool:
                svid = f"{allele.cshl_location}:{allele.cshl_variant}"
                return svid in summary_variant_ids

        else:
            # passed empty list of summary variants; empty result
            return

        index = 0
        seen = set()
        unique_family_variants = bool(kwargs.get("uniqueFamilyVariants"))

        started = time.time()
        try:
            if len(runners) == 0:
                return
            variants_result = QueryResult(
                self.executor, runners, limit=max_variants_count)

            variants_result.start()
            elapsed = time.time() - started

            with closing(variants_result) as variants:
                for variant in variants:
                    if variant is None:
                        continue

                    matched = True
                    for aa in variant.matched_alleles:
                        assert not aa.is_reference_allele
                        if not filter_allele(cast(FamilyAllele, aa)):
                            matched = False
                            break
                    if not matched:
                        continue

                    fvuid = variant.fvuid
                    if unique_family_variants and fvuid in seen:
                        continue
                    seen.add(fvuid)

                    index += 1
                    if max_variants_count and index > max_variants_count:
                        break

                    yield variant
        except GeneratorExit:
            pass
        finally:
            elapsed = time.time() - started
            print(elapsed)

    def query_summary_variants(
        self, study_ids: list[str], kwargs: dict[str, Any],
        max_variants_count: int | None = 10000,
    ) -> Iterable[SummaryVariant]:
        runners = []
        for study_id in study_ids:
            storage = self.find_storage(study_id)
            runner = storage.create_summary_runner(study_id, kwargs)
            if runner is not None:
                runners.append(runner)
        query = QueryResult(
            self.executor, runners, limit=max_variants_count)

        if query is None:
            return
        variants: dict[str, Any] = {}
        limit = kwargs.get("limit")
        started = time.time()
        query.start()
        with closing(query) as variants_result:
            for v in variants_result:
                if v is None:
                    continue

                if v.svuid in variants:
                    existing = variants[v.svuid]
                    fv_count = existing.get_attribute(
                        "family_variants_count")[0]
                    if fv_count is None:
                        continue
                    fv_count += v.get_attribute("family_variants_count")[0]
                    seen_in_status = existing.get_attribute(
                        "seen_in_status")[0]
                    seen_in_status = \
                        seen_in_status | \
                        v.get_attribute("seen_in_status")[0]

                    seen_as_denovo = existing.get_attribute(
                        "seen_as_denovo")[0]
                    seen_as_denovo = \
                        seen_as_denovo or \
                        v.get_attribute("seen_as_denovo")[0]
                    new_attributes = {
                        "family_variants_count": [fv_count],
                        "seen_in_status": [seen_in_status],
                        "seen_as_denovo": [seen_as_denovo],
                    }
                    v.update_attributes(new_attributes)

                variants[v.svuid] = v
                if limit and len(variants) >= limit:
                    break

        elapsed = time.time() - started
        logger.info(
            "processing studies %s elapsed: %.3f",
            study_ids, elapsed)

        yield from variants.values()
