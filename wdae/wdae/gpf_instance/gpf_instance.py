"""Provides wdae GPFInstance class."""
from __future__ import annotations

import hashlib
import logging
import os
import pathlib
import time
from collections.abc import Callable
from importlib.metadata import entry_points
from threading import Lock
from typing import Any, cast

from box import Box
from dae.gpf_instance.gpf_instance import GPFInstance
from dae.utils.fs_utils import find_directory_with_a_file
from dae.utils.helpers import to_response_json
from pheno_tool_api.adapter import PhenoToolAdapter, PhenoToolAdapterBase
from studies.query_transformer import make_query_transformer
from studies.response_transformer import make_response_transformer
from studies.study_wrapper import WDAEAbstractStudy, WDAEStudy, WDAEStudyGroup

from gpf_instance.extension import GPFExtensionBase

logger = logging.getLogger(__name__)
__all__ = ["get_wgpf_instance"]


_GPF_INSTANCE: WGPFInstance | None = None
_GPF_INSTANCE_LOCK = Lock()
_GPF_RECREATED_DATASET_PERM = False


_INSTANCE_TIMESTAMP: float = 0
_PERMISSION_CHANGED_TIMESTAMP: float = 0

_GPF_HASH_STORE: dict[str, str] = {}


def set_instance_timestamp() -> None:
    global _INSTANCE_TIMESTAMP  # pylint: disable=global-statement
    _INSTANCE_TIMESTAMP = time.time()


def get_instance_timestamp() -> float:
    return _INSTANCE_TIMESTAMP


def set_permission_timestamp() -> None:
    global _PERMISSION_CHANGED_TIMESTAMP  # pylint: disable=global-statement
    _PERMISSION_CHANGED_TIMESTAMP = time.time()


def get_permission_timestamp() -> float:
    return _PERMISSION_CHANGED_TIMESTAMP


def permission_update(request_function: Callable) -> Callable:
    def decorated(*args: Any, **kwargs: Any) -> Any:
        response = request_function(*args, **kwargs)
        set_permission_timestamp()
        return response
    return decorated


def get_cacheable_hash(hashable_id: str) -> str | None:
    return _GPF_HASH_STORE.get(hashable_id)


def calc_and_set_cacheable_hash(hashable_id: str, content: str | None) -> None:
    _GPF_HASH_STORE[hashable_id] = calc_cacheable_hash(content)


def set_cacheable_hash(hashable_id: str, hashsum: str) -> None:
    _GPF_HASH_STORE[hashable_id] = hashsum


def calc_cacheable_hash(content: str | None) -> str:
    if content is None:
        content = ""
    return hashlib.md5(content.encode("utf-8")).hexdigest()  # noqa: S324


class WGPFInstance(GPFInstance):
    """GPF instance class for use in wdae."""

    def __init__(
        self, dae_config: dict[str, Any],
        dae_dir: str | pathlib.Path,
        dae_config_path: pathlib.Path,
        **kwargs: dict[str, Any],
    ) -> None:
        self._study_wrappers: dict[str, WDAEStudy] = {}
        self._gp_configuration: dict[str, Any] | None = None
        self.extensions: dict[str, GPFExtensionBase] = {}
        super().__init__(
            cast(Box, dae_config), dae_dir, dae_config_path, **kwargs)

        self.visible_datasets = None
        if self.dae_config.gpfjs and self.dae_config.gpfjs.visible_datasets:
            self.visible_datasets = self.dae_config.gpfjs.visible_datasets
        main_description = self.dae_config.gpfjs.main_description_file
        if not os.path.exists(main_description):
            with open(main_description, "w"):
                os.utime(main_description, None)
        about_description = self.dae_config.gpfjs.about_description_file
        if not os.path.exists(about_description):
            with open(about_description, "w"):
                os.utime(about_description, None)
        set_instance_timestamp()
        set_permission_timestamp()
        self.load_extensions()

    def load_extensions(self) -> None:
        discovered_entries = entry_points(group="wdae.gpf_instance.extensions")
        for entry in discovered_entries:
            extension_class = entry.load()
            self.extensions[entry.name] = extension_class(self)

    def get_pheno_tool_adapter(
        self, study: WDAEAbstractStudy,
    ) -> PhenoToolAdapterBase:
        """Get pheno tool adapter using tool framework."""
        for ext_name, extension in self.extensions.items():
            pheno_tool_adapter = extension.get_tool(study, "pheno_tool")
            if pheno_tool_adapter is not None:
                if not isinstance(pheno_tool_adapter, PhenoToolAdapterBase):
                    raise ValueError(
                        f"{ext_name} returned an invalid pheno tool adapter!")
                return pheno_tool_adapter
        return cast(PhenoToolAdapter, PhenoToolAdapter.make_tool(study))

    @staticmethod
    def build(
        config_filename: str | pathlib.Path | None = None,
        **kwargs: Any,
    ) -> WGPFInstance:
        dae_config, dae_dir, dae_config_path = \
            GPFInstance._build_gpf_config(  # noqa: SLF001
                config_filename)
        return WGPFInstance(dae_config, dae_dir, dae_config_path, **kwargs)

    def get_main_description_path(self) -> str:
        return cast(str, self.dae_config.gpfjs.main_description_file)

    def get_about_description_path(self) -> str:
        return cast(str, self.dae_config.gpfjs.about_description_file)

    def make_wdae_wrapper(self, dataset_id: str) -> WDAEStudy | None:
        """Create and return wdae study wrapper."""
        genotype_data = self.get_genotype_data(dataset_id)
        if genotype_data is not None:
            if genotype_data.config.get("phenotype_data"):
                pheno_id = genotype_data.config.get("phenotype_data")
                phenotype_data = self._pheno_registry.get_phenotype_data(
                    cast(str, pheno_id),
                )
            else:
                phenotype_data = None
        elif self.has_phenotype_data(dataset_id):
            phenotype_data = self.get_phenotype_data(dataset_id)
        else:
            return None

        children_ids = []
        if genotype_data is not None:
            children_ids = [
                gd.study_id
                for gd in genotype_data.get_query_leaf_studies(None)
                if gd.study_id != genotype_data.study_id
            ]
        elif phenotype_data is not None:
            children_ids = [
                child_id for child_id in phenotype_data.get_children_ids()
                if child_id != phenotype_data.pheno_id
            ]

        if len(children_ids) == 0:
            children = None
        else:
            children = [
                self.make_wdae_wrapper(child_id)
                for child_id in children_ids
            ]

        query_transformer = make_query_transformer(self)
        response_transformer = make_response_transformer(self)
        if children is None:
            return WDAEStudy(
                genotype_data, phenotype_data,
                query_transformer=query_transformer,
                response_transformer=response_transformer,
            )
        return WDAEStudyGroup(
            genotype_data, phenotype_data,
            children=cast(list[WDAEStudy], children),
            query_transformer=query_transformer,
            response_transformer=response_transformer,
        )

    def get_wdae_wrapper(self, dataset_id: str) -> WDAEStudy | None:
        """Return wdae study wrapper."""
        wrapper: WDAEStudy | None = None
        if dataset_id not in self._study_wrappers:
            wrapper = self.make_wdae_wrapper(dataset_id)
            if wrapper is not None:
                self._study_wrappers[dataset_id] = wrapper
        else:
            wrapper = self._study_wrappers.get(dataset_id)

        return wrapper

    def get_available_data_ids(self) -> list[str]:
        """Get the IDs of all available data - genotypic and phenotypic."""
        available: set[str] = set()
        for data_id in self.get_genotype_data_ids() \
                + self.get_phenotype_data_ids():
            if data_id in available:
                raise ValueError(f"Duplicate study {data_id}!")
            available.add(data_id)

        result = list(available)

        if self.visible_datasets is None:
            return result
        data_order = self.visible_datasets

        def _ordering(st: str) -> int:
            if st not in data_order:
                return 10_000
            return cast(int, data_order.index(st))

        return sorted(result, key=_ordering)

    def get_visible_datasets(self) -> list[str] | None:
        if self.visible_datasets is None:
            return None
        return [dataset_id for dataset_id
                in self.visible_datasets
                if dataset_id in self.get_available_data_ids()]

    def _gp_find_category_section(
        self, configuration: dict[str, Any], category: str,
    ) -> str | None:
        for gene_set in configuration["geneSets"]:
            if gene_set["category"] == category:
                return "geneSets"
        for gene_score in configuration["geneScores"]:
            if gene_score["category"] == category:
                return "geneScores"
        for dataset in configuration["datasets"]:
            if dataset["id"] == category:
                return "datasets"
        return None

    def get_wdae_gp_configuration(self) -> dict[str, Any] | None:
        if self._gp_configuration is None:
            self.prepare_gp_configuration()
        return self._gp_configuration

    def prepare_gp_configuration(self) -> None:
        """Prepare GP configuration for response ahead of time."""
        # pylint: disable=too-many-branches
        configuration = self.get_gp_configuration()
        if configuration is None:
            self._gp_configuration = {}
            return

        # Camelize snake_cased keys, excluding "datasets"
        # since its keys are dataset IDs
        json_config = to_response_json(configuration)
        # pylint: disable=too-many-nested-blocks
        if len(configuration) > 0:
            if "datasets" in configuration:
                json_config["datasets"] = []

                for dataset_id, dataset in configuration["datasets"].items():
                    study_wrapper = self.get_wdae_wrapper(dataset_id)
                    if study_wrapper is None:
                        logger.error(
                            "could not create a study wrapper for %s",
                            dataset_id)
                        continue

                    person_sets_config = []
                    if "person_sets" in dataset:
                        # Attach person set counts
                        collections = study_wrapper.genotype_data

                        for person_set in dataset["person_sets"]:
                            set_id = person_set["set_name"]
                            collection_id = person_set["collection_name"]
                            description = ""
                            if "description" in person_set:
                                description = person_set["description"]
                            person_set_collection = \
                                collections.person_set_collections[
                                    collection_id
                                ]
                            stats = person_set_collection.get_stats()[set_id]
                            set_name = \
                                person_set_collection.person_sets[set_id].name
                            person_sets_config.append({
                                "id": set_id,
                                "displayName": set_name,
                                "collectionId": collection_id,
                                "description": description,
                                "parentsCount": 0,
                                "childrenCount": stats["children"],
                                "statistics":
                                    to_response_json(dataset)["statistics"],
                            })

                    display_name = dataset.get("display_name") \
                        or study_wrapper.genotype_data.config.get("name") \
                        or dataset_id

                    json_config["datasets"].append({
                        "id": dataset_id,
                        "displayName": display_name,
                        "defaultVisible": True,
                        **to_response_json(dataset),
                        "personSets": person_sets_config,  # overwrite ps
                    })

            assert "order" in json_config

            order = json_config["order"]
            json_config["order"] = [
                {
                    "section": self._gp_find_category_section(json_config, o),
                    "id": o,
                }
                for o in order
            ]

            json_config["pageSize"] = self._gene_profile_db.PAGE_SIZE

        self._gp_configuration = json_config


def get_wgpf_instance_path(
    config_filename: str | pathlib.Path | None = None,
) -> pathlib.Path:
    """Return the path to the GPF instance in use."""
    if _GPF_INSTANCE is not None:
        return pathlib.Path(_GPF_INSTANCE.dae_dir)
    dae_dir: pathlib.Path | None
    if config_filename is not None:
        dae_dir = pathlib.Path(config_filename).parent
        return dae_dir

    from django.conf import settings  # pylint: disable=import-outside-toplevel
    if getattr(settings, "GPF_INSTANCE_CONFIG", None):
        config_filename = pathlib.Path(__file__).parent.joinpath(
            getattr(settings, "GPF_INSTANCE_CONFIG", ""))

        logger.error("GPF instance config: %s", config_filename)
        dae_dir = pathlib.Path(config_filename).parent
        return dae_dir

    if os.environ.get("DAE_DB_DIR"):
        dae_dir = pathlib.Path(os.environ["DAE_DB_DIR"])
        return pathlib.Path(dae_dir)

    dae_dir = find_directory_with_a_file("gpf_instance.yaml")
    if dae_dir is None:
        raise ValueError("unable to locate GPF instance directory")
    return dae_dir


def get_wgpf_instance(
    config_filename: str | pathlib.Path | None = None,
    **kwargs: Any,
) -> WGPFInstance:
    """Load and return a WGPFInstance."""
    # pylint: disable=global-statement

    global _GPF_INSTANCE

    if _GPF_INSTANCE is None:
        with _GPF_INSTANCE_LOCK:
            if _GPF_INSTANCE is None:
                try:
                    gpf_instance = WGPFInstance.build(
                        config_filename, **kwargs)

                    _GPF_INSTANCE = gpf_instance
                except ValueError:
                    logger.exception("unable to create GPF instance")

    from django.conf import settings  # pylint: disable=import-outside-toplevel
    gpf_testing = False
    if hasattr(settings, "GPF_TESTING"):
        gpf_testing = getattr(settings, "GPF_TESTING", False)

    if _GPF_INSTANCE is None and not gpf_testing:
        raise ValueError("can't create the singleton WGPFInstance")
    return _GPF_INSTANCE  # type: ignore


def reload_datasets(gpf_instance: WGPFInstance) -> None:
    """Recreate datasets permissions."""
    # pylint: disable=import-outside-toplevel
    from datasets_api.models import Dataset, DatasetHierarchy

    for data_id in gpf_instance.get_available_data_ids():
        Dataset.recreate_dataset_perm(data_id)
        Dataset.set_broken(data_id, broken=True)

        wdae_study = gpf_instance.get_wdae_wrapper(data_id)
        assert wdae_study is not None
        Dataset.set_broken(data_id, broken=False)
        Dataset.update_name(data_id, wdae_study.name)

        for study_id in wdae_study.get_children_ids(leaves=False):
            if study_id is None or study_id == data_id:
                continue
            Dataset.recreate_dataset_perm(study_id)

    DatasetHierarchy.clear(gpf_instance.instance_id)

    for data_id in gpf_instance.get_available_data_ids():
        wdae_study = gpf_instance.get_wdae_wrapper(data_id)
        DatasetHierarchy.add_relation(
            gpf_instance.instance_id, data_id, data_id,
        )
        assert wdae_study is not None
        direct_descendants = wdae_study.get_children_ids(leaves=False)
        for study_id in wdae_study.get_children_ids():
            if study_id == data_id:
                continue
            is_direct = study_id in direct_descendants
            DatasetHierarchy.add_relation(
                gpf_instance.instance_id, data_id, study_id,
                direct=is_direct,
            )


def recreated_dataset_perm(gpf_instance: WGPFInstance) -> None:
    """Recreate dataset permisions for a GPF instance."""
    # pylint: disable=global-statement
    global _GPF_RECREATED_DATASET_PERM
    if gpf_instance is None:
        logger.warning("GPF instance is not loaded")
        return

    if _GPF_RECREATED_DATASET_PERM:
        return

    with _GPF_INSTANCE_LOCK:
        # assert _GPF_INSTANCE is not None

        if not _GPF_RECREATED_DATASET_PERM:
            reload_datasets(gpf_instance)
            _GPF_RECREATED_DATASET_PERM = True
