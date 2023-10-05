"""Provides wdae GPFInstance class."""
from __future__ import annotations

import logging
import pathlib
import os
from typing import Optional, List, Dict, Any, Union
from threading import Lock
from functools import cached_property

from studies.study_wrapper import StudyWrapper, RemoteStudyWrapper, \
    StudyWrapperBase
from studies.remote_study_db import RemoteStudyDB

from enrichment_api.enrichment_builder import \
    EnrichmentBuilder, RemoteEnrichmentBuilder

from remote.gene_sets_db import RemoteGeneSetsDb
from remote.denovo_gene_sets_db import RemoteDenovoGeneSetsDb
from remote.rest_api_client import RESTClient
from remote.genomic_scores_db import RemoteGenomicScoresDb

from dae.utils.fs_utils import find_directory_with_a_file
from dae.gpf_instance.gpf_instance import GPFInstance
from dae.enrichment_tool.tool import EnrichmentTool
from dae.enrichment_tool.event_counters import CounterBase
from dae.common_reports.common_report import CommonReport


logger = logging.getLogger(__name__)
__all__ = ["get_wgpf_instance"]


_GPF_INSTANCE: Optional[WGPFInstance] = None
_GPF_INSTANCE_LOCK = Lock()
_GPF_RECREATED_DATASET_PERM = False


class WGPFInstance(GPFInstance):
    """GPF instance class for use in wdae."""

    def __init__(self, dae_config, dae_dir, **kwargs):
        self._remote_study_db: Optional[RemoteStudyDB] = None
        self._clients: List[RESTClient] = []
        self._study_wrappers: Dict[str, StudyWrapperBase] = {}
        super().__init__(dae_config, dae_dir, **kwargs)

    @staticmethod
    def build(
        config_filename: Optional[Union[str, pathlib.Path]] = None,
        **kwargs: Any
    ) -> WGPFInstance:
        dae_config, dae_dir = GPFInstance._build_gpf_config(config_filename)
        return WGPFInstance(dae_config, dae_dir, **kwargs)

    def load_remotes(self):
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
                        gpf_prefix=remote.get("gpf_prefix", None)
                    )
                    self._clients.append(client)

                except ConnectionError as err:
                    logger.error(err)
                    logger.error("Failed to create remote %s", remote["id"])

        self._remote_study_db = RemoteStudyDB(self._clients)

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
    def gene_sets_db(self):
        logger.debug("creating new instance of GeneSetsDb")
        self.load_remotes()
        gene_sets_db = super().gene_sets_db
        return RemoteGeneSetsDb(self._clients, gene_sets_db)

    @cached_property
    def denovo_gene_sets_db(self):
        self.load_remotes()
        denovo_gene_sets_db = super().denovo_gene_sets_db
        return RemoteDenovoGeneSetsDb(self._clients, denovo_gene_sets_db)

    @cached_property
    def genomic_scores_db(self):
        self.load_remotes()
        genomic_scores_db = super().genomic_scores_db
        db = RemoteGenomicScoresDb(self._clients, genomic_scores_db)
        return db

    def register_genotype_data(self, genotype_data):
        super().register_genotype_data(genotype_data)

        logger.debug("genotype data config; %s", genotype_data.study_id)

        study_wrapper = StudyWrapper(
            genotype_data,
            self._pheno_db,
            self.gene_scores_db
        )
        return study_wrapper

    def make_wdae_wrapper(self, dataset_id: str) -> Optional[StudyWrapperBase]:
        """Create and return wdae study wrapper."""
        genotype_data = self.get_genotype_data(dataset_id)
        if genotype_data is None:
            return None

        if genotype_data.is_remote:
            return RemoteStudyWrapper(genotype_data)
        return StudyWrapper(
            genotype_data, self._pheno_db, self.gene_scores_db
        )

    def get_wdae_wrapper(self, dataset_id):
        """Return wdae study wrapper."""
        if dataset_id not in self._study_wrappers:
            wrapper = self.make_wdae_wrapper(dataset_id)
            if wrapper is not None:
                self._study_wrappers[dataset_id] = wrapper
        else:
            wrapper = self._study_wrappers.get(dataset_id, None)

        return wrapper

    def get_genotype_data_ids(self, local_only=False):
        if local_only:
            return list(super().get_genotype_data_ids())

        return (
            list(super().get_genotype_data_ids()) + self.remote_studies
        )

    def get_genotype_data(self, genotype_data_id):
        genotype_data = super().get_genotype_data(genotype_data_id)
        if genotype_data is not None:
            return genotype_data
        assert self._remote_study_db is not None
        genotype_data = self._remote_study_db\
            .get_genotype_data(genotype_data_id)
        return genotype_data

    def get_genotype_data_config(self, genotype_data_id):
        genotype_data_config = \
            super().get_genotype_data_config(genotype_data_id)
        if genotype_data_config is not None:
            return genotype_data_config
        assert self._remote_study_db is not None
        return self._remote_study_db\
            .get_genotype_data_config(genotype_data_id)

    def get_common_report(self, study_id):
        common_report = \
            super().get_common_report(study_id)

        if common_report is not None:
            return common_report

        if study_id not in self.remote_study_clients:
            return None

        client = self.remote_study_clients[study_id]
        remote_study_id = self.remote_study_ids[study_id]
        common_report = client.get_common_report(remote_study_id, full=True)
        return CommonReport(common_report)

    def get_study_enrichment_config(self, dataset_id):
        result = \
            super().get_study_enrichment_config(dataset_id)

        if not result:
            study_wrapper = self.get_wdae_wrapper(dataset_id)
            if study_wrapper is None:
                return None
            if "enrichment" in study_wrapper.config:
                result = study_wrapper.config["enrichment"]

        return result

    def get_enrichment_tool(
            self, enrichment_config, dataset_id,
            background_name, counting_name=None):
        """Build and return enrichment tool."""
        if (
            background_name is None
            or not self.has_background(
                dataset_id, background_name
            )
        ):
            background_name = enrichment_config.default_background_model
        if not counting_name:
            counting_name = enrichment_config.default_counting_model

        background = self.get_study_background(
            dataset_id, background_name
        )

        if background is None:
            logger.warning("Background %s not found!", background_name)

        counter = CounterBase.counters()[counting_name]()
        enrichment_tool = EnrichmentTool(
            enrichment_config, background, counter
        )

        return enrichment_tool

    def _create_local_enrichment_builder(
            self, dataset_id, background_name, counting_name,
            gene_syms):
        dataset = self.get_genotype_data(dataset_id)
        enrichment_config = GPFInstance.get_study_enrichment_config(
            self,
            dataset_id
        )
        if enrichment_config is None:
            return None
        enrichment_tool = self.get_enrichment_tool(
            enrichment_config, dataset_id, background_name, counting_name)
        if enrichment_tool.background is None:
            return None

        builder = EnrichmentBuilder(dataset, enrichment_tool, gene_syms)
        return builder

    def create_enrichment_builder(
            self, dataset_id, background_name, counting_name,
            gene_syms):
        """Create an enrichment builder."""
        builder = self._create_local_enrichment_builder(
            dataset_id, background_name, counting_name, gene_syms)
        if not builder:
            dataset = self.get_wdae_wrapper(dataset_id)
            if dataset.is_remote is False:
                logger.warning("WARNING: Using is_remote")
                logger.warning(
                    "WARNING: Failed to create local enrichment builder!\n"
                    "dataset: %s, "
                    "requested background: %s, "
                    "requested counting name: %s",
                    dataset_id, background_name, counting_name
                )
            builder = RemoteEnrichmentBuilder(
                dataset, dataset.rest_client,
                background_name, counting_name,
                gene_syms)

        return builder

    @property
    def remote_studies(self):
        if self._remote_study_db is None:
            return []
        return list(self._remote_study_db.get_genotype_data_ids())

    def get_all_denovo_gene_sets(self, types, datasets, collection_id):
        # pylint: disable=arguments-differ
        return self.denovo_gene_sets_db.get_all_gene_sets(
            types, datasets, collection_id)

    def get_denovo_gene_set(self, gene_set_id, types, datasets, collection_id):
        # pylint: disable=arguments-differ
        return self.denovo_gene_sets_db.get_gene_set(
            gene_set_id, types, datasets, collection_id)

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


def get_wgpf_instance_path(config_filename=None):
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


def get_wgpf_instance(config_filename=None, **kwargs) -> WGPFInstance:
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


def reload_datasets(gpf_instance):
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

    DatasetHierarchy.clear()
    datasets = gpf_instance.get_genotype_data_ids()
    for genotype_data_id in datasets:
        genotype_data = gpf_instance.get_genotype_data(genotype_data_id)
        if genotype_data is None:
            logger.error(
                "unable to find study %s; skipping...", genotype_data_id)
            continue
        direct_descendants = genotype_data.get_studies_ids(leaves=False)
        for study_id in genotype_data.get_studies_ids():
            if study_id == genotype_data_id:
                continue
            is_direct = study_id in direct_descendants
            DatasetHierarchy.add_relation(
                genotype_data_id, study_id, is_direct
            )


def recreated_dataset_perm(gpf_instance):
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
