"""Provides wdae GPFInstance class."""
from __future__ import annotations

import hashlib
import logging
import os
import pathlib
import time
from collections.abc import Callable
from threading import Lock
from typing import Any, cast

from box import Box
from studies.study_wrapper import StudyWrapper, StudyWrapperBase

from dae.gpf_instance.gpf_instance import GPFInstance
from dae.studies.study import GenotypeData
from dae.utils.fs_utils import find_directory_with_a_file
from dae.utils.helpers import to_response_json

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
        **kwargs: dict[str, Any],
    ) -> None:
        self._remote_study_db: None = None
        self._study_wrappers: dict[
            str, StudyWrapper,
        ] = {}
        self._gp_configuration: dict[str, Any] | None = None
        super().__init__(cast(Box, dae_config), dae_dir, **kwargs)

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

    @staticmethod
    def build(
        config_filename: str | pathlib.Path | None = None,
        **kwargs: Any,
    ) -> WGPFInstance:
        dae_config, dae_dir = GPFInstance._build_gpf_config(  # noqa: SLF001
            config_filename)
        return WGPFInstance(dae_config, dae_dir, **kwargs)

    def get_main_description_path(self) -> str:
        return cast(str, self.dae_config.gpfjs.main_description_file)

    def get_about_description_path(self) -> str:
        return cast(str, self.dae_config.gpfjs.about_description_file)

    def register_genotype_data(
        self, genotype_data: GenotypeData,
        study_wrapper: StudyWrapperBase | None = None,
    ) -> None:
        super().register_genotype_data(genotype_data)

        logger.debug("genotype data config; %s", genotype_data.study_id)

        if study_wrapper is None:
            study_wrapper = StudyWrapper(
                genotype_data,
                self._pheno_registry,
                self.gene_scores_db,
                self,
            )
        self._study_wrappers[
            genotype_data.study_id] = study_wrapper  # type: ignore

    def make_wdae_wrapper(
        self, dataset_id: str,
    ) -> StudyWrapper | None:
        """Create and return wdae study wrapper."""
        genotype_data = self.get_genotype_data(dataset_id)
        if genotype_data is None:
            return None

        return StudyWrapper(
            genotype_data, self._pheno_registry, self.gene_scores_db, self,
        )

    def get_wdae_wrapper(
        self, dataset_id: str,
    ) -> StudyWrapper | None:
        """Return wdae study wrapper."""
        wrapper: StudyWrapper | None = None
        if dataset_id not in self._study_wrappers:
            wrapper = self.make_wdae_wrapper(dataset_id)
            if wrapper is not None:
                self._study_wrappers[dataset_id] = wrapper
        else:
            wrapper = self._study_wrappers.get(dataset_id)

        return wrapper

    def get_genotype_data_ids(self) -> list[str]:
        result = list(super().get_genotype_data_ids())

        if self.visible_datasets is None:
            return result
        genotype_data_order = self.visible_datasets
        if genotype_data_order is None:
            genotype_data_order = []

        def _ordering(st: str) -> int:
            if st not in genotype_data_order:
                return 10_000
            return cast(int, genotype_data_order.index(st))

        return sorted(result, key=_ordering)

    @property
    def remote_studies(self) -> list[str]:
        if self._remote_study_db is None:
            return []
        return list(self._remote_study_db.get_genotype_data_ids())

    def get_visible_datasets(self) -> list[str] | None:
        if self.visible_datasets is None:
            return None
        all_datasets = self.get_genotype_data_ids()
        return [
            dataset_id for dataset_id
            in self.visible_datasets
            if dataset_id in all_datasets
        ]

    def _gp_find_category_section(
        self, configuration: dict[str, Any], category: str,
    ) -> str | None:
        for gene_set in configuration["geneSets"]:
            if gene_set["category"] == category:
                return "geneSets"
        for genomic_score in configuration["genomicScores"]:
            if genomic_score["category"] == category:
                return "genomicScores"
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

                    display_name = dataset.get("display_name")
                    if display_name is None:
                        display_name = study_wrapper.config.get("name")
                    if display_name is None:
                        display_name = dataset_id

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
                    logger.warning("unable to create GPF instance")

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

    for genotype_data_id in gpf_instance.get_genotype_data_ids():
        Dataset.recreate_dataset_perm(genotype_data_id)
        Dataset.set_broken(genotype_data_id, broken=True)

        genotype_data = gpf_instance.get_genotype_data(genotype_data_id)
        if genotype_data is None:
            continue
        Dataset.set_broken(genotype_data_id, broken=False)
        Dataset.update_name(genotype_data_id, genotype_data.name)
        if not genotype_data.studies:
            continue

        for study_id in genotype_data.get_studies_ids(leaves=False):
            if study_id is None or study_id == genotype_data_id:
                continue
            Dataset.recreate_dataset_perm(study_id)

    DatasetHierarchy.clear(gpf_instance.instance_id)
    datasets = gpf_instance.get_genotype_data_ids()
    for genotype_data_id in datasets:
        genotype_data = gpf_instance.get_genotype_data(genotype_data_id)
        if genotype_data is None:
            logger.error(
                "unable to find study %s; skipping...", genotype_data_id)
            continue
        DatasetHierarchy.add_relation(
            gpf_instance.instance_id, genotype_data_id, genotype_data_id,
        )
        direct_descendants = genotype_data.get_studies_ids(leaves=False)
        for study_id in genotype_data.get_studies_ids():
            if study_id == genotype_data_id:
                continue
            is_direct = study_id in direct_descendants
            DatasetHierarchy.add_relation(
                gpf_instance.instance_id, genotype_data_id, study_id,
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
