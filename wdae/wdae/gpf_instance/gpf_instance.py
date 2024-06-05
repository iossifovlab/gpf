"""Provides wdae GPFInstance class."""
from __future__ import annotations

import logging
import os
import time
import pathlib
from functools import cached_property
from threading import Lock
from typing import Any, Dict, Optional, Union, cast

from box import Box
from remote.denovo_gene_sets_db import RemoteDenovoGeneSetsDb
from remote.gene_sets_db import RemoteGeneSetsDb
from remote.genomic_scores_registry import RemoteGenomicScoresRegistry
from remote.rest_api_client import RESTClient
from studies.remote_study import RemoteGenotypeData
from studies.remote_study_db import RemoteStudyDB
from studies.study_wrapper import RemoteStudyWrapper, StudyWrapper

from dae.common_reports.common_report import CommonReport
from dae.gpf_instance.gpf_instance import GPFInstance
from dae.studies.study import GenotypeData
from dae.utils.fs_utils import find_directory_with_a_file
from dae.utils.helpers import to_response_json

logger = logging.getLogger(__name__)
__all__ = ["get_wgpf_instance"]


_GPF_INSTANCE: Optional[WGPFInstance] = None
_GPF_INSTANCE_LOCK = Lock()
_GPF_RECREATED_DATASET_PERM = False


_INSTANCE_TIMESTAMP: float = 0
_PERMISSION_CHANGED_TIMESTAMP: float = 0

def set_instance_timestamp() -> None:
    global _INSTANCE_TIMESTAMP
    _INSTANCE_TIMESTAMP = time.time()

def get_instance_timestamp() -> float:
    global _INSTANCE_TIMESTAMP
    return _INSTANCE_TIMESTAMP

def set_permission_timestamp() -> None:
    global _PERMISSION_CHANGED_TIMESTAMP
    print(time.time())
    _PERMISSION_CHANGED_TIMESTAMP = time.time()

def get_permission_timestamp() -> float:
    global _PERMISSION_CHANGED_TIMESTAMP
    return _PERMISSION_CHANGED_TIMESTAMP

def permission_update(request_function):
    def decorated(*args, **kwargs):
        response = request_function(*args, **kwargs)
        set_permission_timestamp()
        return response
    return decorated

class WGPFInstance(GPFInstance):
    """GPF instance class for use in wdae."""

    def __init__(
        self, dae_config: dict[str, Any],
        dae_dir: Union[str, pathlib.Path],
        **kwargs: dict[str, Any],
    ) -> None:
        self._remote_study_db: Optional[RemoteStudyDB] = None
        self._clients: Dict[str, RESTClient] = {}
        self._study_wrappers: Dict[
            str, Union[StudyWrapper, RemoteStudyWrapper],
        ] = {}
        self._gp_configuration: Optional[dict[str, Any]] = None
        self._gp_table_configuration: Optional[dict[str, Any]] = None
        super().__init__(cast(Box, dae_config), dae_dir, **kwargs)
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
        config_filename: Optional[Union[str, pathlib.Path]] = None,
        **kwargs: Any,
    ) -> WGPFInstance:
        dae_config, dae_dir = GPFInstance._build_gpf_config(config_filename)
        return WGPFInstance(dae_config, dae_dir, **kwargs)

    def load_remotes(self) -> None:
        """Load remote instances for use in GPF federation."""
        if self._remote_study_db is not None:
            return

        remotes = self.dae_config.remotes

        if remotes is not None:
            for remote in remotes:
                logger.info("Creating remote %s", remote)
                try:
                    client = RESTClient(
                        remote["id"],
                        remote["host"],
                        remote["credentials"],
                        base_url=remote["base_url"],
                        port=remote.get("port", None),
                        protocol=remote.get("protocol", None),
                        gpf_prefix=remote.get("gpf_prefix", None),
                    )
                    self._clients[client.remote_id] = client

                except ConnectionError as err:
                    logger.error(err)
                    logger.error("Failed to create remote %s", remote["id"])

        self._remote_study_db = RemoteStudyDB(self._clients)

    def get_main_description_path(self) -> str:
        return cast(str, self.dae_config.gpfjs.main_description_file)

    def get_about_description_path(self) -> str:
        return cast(str, self.dae_config.gpfjs.about_description_file)

    def get_remote_client(self, remote_id: str) -> Optional[RESTClient]:
        return self._clients.get(remote_id)

    @property
    def remote_study_clients(self) -> Dict[str, RESTClient]:
        if self._remote_study_db is None:
            raise ValueError("remote study db not initialized.")
        return self._remote_study_db.remote_study_clients

    @property
    def remote_study_ids(self) -> Dict[str, str]:
        """Return remote studies IDs.

        Returns a dictionary mapping local prefixed remote study ids
        to their real ids on the remote.
        """
        if self._remote_study_db is None:
            raise ValueError("remote study db not initialized.")
        return self._remote_study_db.remote_study_ids

    @cached_property
    def gene_sets_db(self) -> RemoteGeneSetsDb:
        logger.debug("creating new instance of GeneSetsDb")
        self.load_remotes()
        gene_sets_db = super().gene_sets_db
        return RemoteGeneSetsDb(self._clients, gene_sets_db)

    @cached_property
    def denovo_gene_sets_db(self) -> RemoteDenovoGeneSetsDb:
        self.load_remotes()
        denovo_gene_sets_db = super().denovo_gene_sets_db
        return RemoteDenovoGeneSetsDb(self._clients, denovo_gene_sets_db)

    @cached_property
    def genomic_scores(self) -> RemoteGenomicScoresRegistry:
        self.load_remotes()
        genomic_scores = super().genomic_scores
        registry = RemoteGenomicScoresRegistry(self._clients, genomic_scores)
        return registry

    def register_genotype_data(
        self, genotype_data: GenotypeData,
    ) -> None:
        super().register_genotype_data(genotype_data)

        logger.debug("genotype data config; %s", genotype_data.study_id)

        study_wrapper = StudyWrapper(
            genotype_data,
            self._pheno_registry,
            self.gene_scores_db,
            self,
        )
        self._study_wrappers[genotype_data.study_id] = study_wrapper

    def make_wdae_wrapper(
        self, dataset_id: str,
    ) -> Optional[Union[StudyWrapper, RemoteStudyWrapper]]:
        """Create and return wdae study wrapper."""
        genotype_data = self.get_genotype_data(dataset_id)
        if genotype_data is None:
            return None

        if genotype_data.is_remote:
            return RemoteStudyWrapper(cast(RemoteGenotypeData, genotype_data))
        return StudyWrapper(
            genotype_data, self._pheno_registry, self.gene_scores_db, self,
        )

    def get_wdae_wrapper(
        self, dataset_id: str,
    ) -> Optional[Union[StudyWrapper, RemoteStudyWrapper]]:
        """Return wdae study wrapper."""
        wrapper: Optional[Union[StudyWrapper, RemoteStudyWrapper]] = None
        if dataset_id not in self._study_wrappers:
            wrapper = self.make_wdae_wrapper(dataset_id)
            if wrapper is not None:
                self._study_wrappers[dataset_id] = wrapper
        else:
            wrapper = self._study_wrappers.get(dataset_id)

        return wrapper

    def get_genotype_data_ids(self, local_only: bool = False) -> list[str]:
        result = list(super().get_genotype_data_ids())
        if not local_only:
            result.extend(self.remote_studies)

        if self.dae_config.gpfjs is None or \
                not self.dae_config.gpfjs.visible_datasets:
            return result
        genotype_data_order = self.dae_config.gpfjs.visible_datasets
        if genotype_data_order is None:
            genotype_data_order = []

        def _ordering(st: str) -> int:
            if st not in genotype_data_order:
                return 10_000
            return cast(int, genotype_data_order.index(st))

        return sorted(result, key=_ordering)

    def get_genotype_data(
        self, genotype_data_id: str,
    ) -> Union[GenotypeData, RemoteGenotypeData]:
        genotype_data = super().get_genotype_data(genotype_data_id)
        if genotype_data is not None:
            return genotype_data
        assert self._remote_study_db is not None
        genotype_data = self._remote_study_db\
            .get_genotype_data(genotype_data_id)
        return genotype_data

    def get_genotype_data_config(self, genotype_data_id: str) -> Box:
        genotype_data_config = \
            super().get_genotype_data_config(genotype_data_id)
        if genotype_data_config is not None:
            return genotype_data_config
        assert self._remote_study_db is not None
        return cast(
            Box,
            self._remote_study_db.get_genotype_data_config(genotype_data_id),
        )

    def get_common_report(self, study_id: str) -> Optional[CommonReport]:
        common_report = \
            super().get_common_report(study_id)

        if common_report is not None:
            return common_report

        if study_id not in self.remote_study_clients:
            return None

        client = self.remote_study_clients[study_id]
        remote_study_id = self.remote_study_ids[study_id]
        remote_common_report = client.get_common_report(
            remote_study_id, full=True)
        return CommonReport(remote_common_report)

    @property
    def remote_studies(self) -> list[str]:
        if self._remote_study_db is None:
            return []
        return list(self._remote_study_db.get_genotype_data_ids())

    def get_all_denovo_gene_sets(
        self, types: dict[str, Any],
        datasets: list[Any], collection_id: str,
    ) -> list[dict[str, Any]]:
        # pylint: disable=arguments-differ
        return cast(
            list[dict[str, Any]],
            self.denovo_gene_sets_db.get_all_gene_sets(
                types, datasets, collection_id,
            ),
        )

    def get_denovo_gene_set(
        self, gene_set_id: str,
        types: dict[str, Any],
        datasets: list[Any],
        collection_id: str,
    ) -> dict[str, Any]:
        # pylint: disable=arguments-differ
        return cast(
            dict[str, Any],
            self.denovo_gene_sets_db.get_gene_set(
                gene_set_id, types, datasets, collection_id,
            ),
        )

    def get_visible_datasets(self) -> Optional[list[str]]:
        if self.dae_config.gpfjs is None:
            return None
        if not self.dae_config.gpfjs.visible_datasets:
            return None
        all_datasets = self.get_genotype_data_ids()
        return [
            dataset_id for dataset_id
            in self.dae_config.gpfjs.visible_datasets
            if dataset_id in all_datasets
        ]

    def _gp_find_category_section(
        self, configuration: dict[str, Any], category: str,
    ) -> Optional[str]:
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

    def get_wdae_gp_configuration(self) -> Optional[dict[str, Any]]:
        if self._gp_configuration is None:
            self.prepare_gp_configuration()
        return self._gp_configuration

    def get_wdae_gp_table_configuration(self) -> Optional[dict[str, Any]]:
        if self._gp_table_configuration is None:
            self.prepare_gp_configuration()
        return self._gp_table_configuration

    def prepare_gp_configuration(self) -> None:
        """Prepare GP configuration for response ahead of time."""
        # pylint: disable=too-many-branches
        configuration = self.get_gp_configuration()
        if configuration is None:
            self._gp_configuration = {}
            self._gp_table_configuration = {}
            return

        # Camelize snake_cased keys, excluding "datasets"
        # since its keys are dataset IDs
        json_config = to_response_json(configuration)
        self._gp_configuration = json_config
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

                    if "person_sets" in dataset:
                        # Attach person set counts
                        person_sets_config = []
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
                                "parentsCount": stats["parents"],
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

        self._gp_table_configuration = {}
        if len(configuration) > 0:
            table_config = {
                "defaultDataset": configuration.get("default_dataset"),
                "columns": [],
                "pageSize": self._gene_profile_db.PAGE_SIZE,
            }

            table_config["columns"].append(
                column("geneSymbol", "Gene", clickable="createTab"),
            )

            for category in configuration["gene_sets"]:
                table_config["columns"].append(column(
                    f"{category['category']}_rank",
                    category["display_name"],
                    visible=category.get("default_visible", True),
                    meta=category.get("meta"),
                    sortable=True,
                    columns=[column(
                        f"{category['category']}_rank.{gene_set['set_id']}",
                        gene_set["set_id"],
                        visible=gene_set.get("default_visible", True),
                        meta=gene_set.get("meta"),
                        display_vertical=True,
                        sortable=True) for gene_set in category["sets"]
                    ],
                ))

            for category in configuration["genomic_scores"]:
                table_config["columns"].append(column(
                    category["category"],
                    category["display_name"],
                    visible=category.get("default_visible", True),
                    meta=category.get("meta"),
                    columns=[column(
                        f"{category['category']}."
                        f"{genomic_score['score_name']}",
                        genomic_score["score_name"],
                        visible=genomic_score.get("default_visible", True),
                        meta=genomic_score.get("meta"),
                        display_vertical=True,
                        sortable=True) for genomic_score in category["scores"]
                    ],
                ))

            if "datasets" in configuration:
                for dataset_id, dataset in configuration["datasets"].items():
                    study_wrapper = self.get_wdae_wrapper(dataset_id)
                    if study_wrapper is None:
                        logger.error("missing dataset %s", dataset_id)
                        continue
                    display_name = dataset.get("display_name") \
                        or study_wrapper.config.get("name") \
                        or dataset_id
                    dataset_col = column(
                        f"{dataset_id}", display_name,
                        visible=dataset.get("default_visible", True),
                        meta=dataset.get("meta"),
                    )
                    for person_set in dataset.get("person_sets", []):
                        set_id = person_set["set_name"]
                        collection_id = person_set["collection_name"]
                        person_set_collection = \
                            study_wrapper.genotype_data.person_set_collections[
                                collection_id
                            ]
                        set_name = \
                            person_set_collection.person_sets[set_id].name
                        stats = person_set_collection.get_stats()[set_id]
                        dataset_col["columns"].append(column(
                            f"{dataset_id}.{set_id}",
                            f"{set_name} ({stats['children']})",
                            visible=person_set.get("default_visible", True),
                            meta=person_set.get("meta"),
                            columns=[column(
                                f"{dataset_id}.{set_id}.{statistic['id']}",
                                statistic["display_name"],
                                visible=statistic.get("default_visible", True),
                                meta=statistic.get("meta"),
                                clickable="goToQuery",
                                sortable=True)

                                for statistic in dataset["statistics"]
                            ],
                        ))
                    table_config["columns"].append(dataset_col)

            if configuration.get("order"):
                category_order = ["geneSymbol", *configuration["order"]]
                table_config["columns"].sort(
                    key=lambda col: category_order.index(col["id"]),
                )

            self._gp_table_configuration = table_config


def column(
    col_id: str,
    display_name: str,
    visible: bool = True,
    clickable: Optional[str] = None,
    display_vertical: bool = False,
    sortable: bool = False,
    columns: Optional[list[dict[str, Any]]] = None,
    meta: Optional[str] = None,
) -> dict[str, Any]:
    """Build columns descriptions."""
    if columns is None:
        columns = []
    return {
        "id": col_id,
        "displayName": display_name,
        "visible": visible,
        "displayVertical": display_vertical,
        "sortable": sortable,
        "clickable": clickable,
        "columns": columns,
        "meta": meta,
    }


def get_wgpf_instance_path(
    config_filename: Union[str, pathlib.Path, None] = None,
) -> pathlib.Path:
    """Return the path to the GPF instance in use."""
    if _GPF_INSTANCE is not None:
        return pathlib.Path(_GPF_INSTANCE.dae_dir)
    dae_dir: Optional[pathlib.Path]
    if config_filename is not None:
        dae_dir = pathlib.Path(config_filename).parent
        return dae_dir

    from django.conf import settings  # pylint: disable=import-outside-toplevel
    if getattr(settings, "GPF_INSTANCE_CONFIG", None):
        config_filename = pathlib.Path(__file__).parent.joinpath(
            settings.GPF_INSTANCE_CONFIG)

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
    config_filename: Union[str, pathlib.Path, None] = None,
    **kwargs: dict[str, Any],
) -> WGPFInstance:
    """Load and return a WGPFInstance."""
    # pylint: disable=global-statement
    global _GPF_INSTANCE

    if _GPF_INSTANCE is None:
        with _GPF_INSTANCE_LOCK:
            if _GPF_INSTANCE is None:
                gpf_instance = WGPFInstance.build(config_filename, **kwargs)
                gpf_instance.load_remotes()

                _GPF_INSTANCE = gpf_instance

    if _GPF_INSTANCE is None:
        raise ValueError("can't create the singleton WGPFInstance")

    return _GPF_INSTANCE


def reload_datasets(gpf_instance: WGPFInstance) -> None:
    """Recreate datasets permissions."""
    # pylint: disable=import-outside-toplevel
    from datasets_api.models import Dataset, DatasetHierarchy
    for genotype_data_id in gpf_instance.get_genotype_data_ids():
        Dataset.recreate_dataset_perm(genotype_data_id)
        Dataset.set_broken(genotype_data_id, True)

        genotype_data = gpf_instance.get_genotype_data(genotype_data_id)
        if genotype_data is None:
            continue
        Dataset.set_broken(genotype_data_id, False)
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
                gpf_instance.instance_id, genotype_data_id, study_id, is_direct,
            )


def recreated_dataset_perm(gpf_instance: WGPFInstance) -> None:
    """Recreate dataset permisions for a GPF instance."""
    # pylint: disable=global-statement
    global _GPF_RECREATED_DATASET_PERM

    if _GPF_RECREATED_DATASET_PERM:
        return

    with _GPF_INSTANCE_LOCK:
        assert _GPF_INSTANCE is not None

        if not _GPF_RECREATED_DATASET_PERM:
            reload_datasets(gpf_instance)
            _GPF_RECREATED_DATASET_PERM = True
