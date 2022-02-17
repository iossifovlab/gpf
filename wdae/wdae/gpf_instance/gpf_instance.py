import logging
import os
from typing import Optional, List, Dict
from threading import Lock

from django.conf import settings

from dae.gpf_instance.gpf_instance import GPFInstance, cached
from studies.study_wrapper import StudyWrapper, RemoteStudyWrapper, \
    StudyWrapperBase
from studies.remote_study_db import RemoteStudyDB

from remote.gene_sets_db import RemoteGeneSetsDb
from remote.denovo_gene_sets_db import RemoteDenovoGeneSetsDb
from remote.rest_api_client import RESTClient

from dae.enrichment_tool.tool import EnrichmentTool
from dae.enrichment_tool.event_counters import CounterBase
from enrichment_api.enrichment_builder import \
    EnrichmentBuilder, RemoteEnrichmentBuilder
from dae.utils.dae_utils import get_pheno_browser_images_dir


logger = logging.getLogger(__name__)
__all__ = ["get_gpf_instance"]


_gpf_instance = None
_gpf_recreated_dataset_perm = False
_gpf_instance_lock = Lock()


class WGPFInstance(GPFInstance):
    def __init__(self, *args, **kwargs):
        self._remote_study_db = None
        self._clients: List[RESTClient] = list()
        self._study_wrappers: Dict[str, StudyWrapperBase] = dict()
        super().__init__(*args, **kwargs)
        self._load_remotes()

    def _load_remotes(self):
        if self._remote_study_db is not None:
            return

        remotes = self.dae_config.remotes

        if remotes is not None:
            for remote in remotes:
                logger.info(f"Creating remote {remote}")
                try:
                    client = RESTClient(
                        remote["id"],
                        remote["host"],
                        remote["user"],
                        remote["password"],
                        base_url=remote["base_url"],
                        port=remote.get("port", None),
                        protocol=remote.get("protocol", None),
                        gpf_prefix=remote.get("gpf_prefix", None)
                    )
                    self._clients.append(client)
                except ConnectionError as err:
                    logger.error(err)
                    logger.error(f"Failed to create remote {remote['id']}")

        self._remote_study_db = RemoteStudyDB(self._clients)

    @property
    def remote_study_clients(self) -> Dict[str, RESTClient]:
        return self._remote_study_db._remote_study_clients

    @property
    def remote_study_ids(self) -> Dict[str, str]:
        """
        Returns a dictionary mapping local prefixed remote study ids
        to their real ids on the remote.
        """
        return self._remote_study_db._remote_study_ids

    @property  # type: ignore
    @cached
    def gene_sets_db(self):
        logger.debug("creating new instance of GeneSetsDb")
        self._load_remotes()
        gene_sets_db = super().gene_sets_db
        return RemoteGeneSetsDb(self._clients, gene_sets_db)

    @property  # type: ignore
    @cached
    def denovo_gene_sets_db(self):
        self._load_remotes()
        denovo_gene_sets_db = super().denovo_gene_sets_db
        return RemoteDenovoGeneSetsDb(self._clients, denovo_gene_sets_db)

    def register_genotype_data(self, genotype_data):
        super().register_genotype_data(genotype_data)

        logger.debug(f"genotype data config; {genotype_data.study_id}")

        study_wrapper = StudyWrapper(
            genotype_data,
            self._pheno_db,
            self.gene_weights_db
        )
        return study_wrapper

    def make_wdae_wrapper(self, dataset_id: str) -> Optional[StudyWrapperBase]:
        genotype_data = self.get_genotype_data(dataset_id)
        if genotype_data is None:
            return None

        if genotype_data.is_remote:
            return RemoteStudyWrapper(genotype_data)
        else:
            return StudyWrapper(
                genotype_data, self._pheno_db, self.gene_weights_db
            )

    def get_wdae_wrapper(self, dataset_id):
        if dataset_id not in self._study_wrappers.keys():
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

    def get_genotype_data(self, dataset_id):
        genotype_data = super().get_genotype_data(dataset_id)
        if genotype_data is not None:
            return genotype_data

        genotype_data = self._remote_study_db.get_genotype_data(dataset_id)
        return genotype_data

    def get_genotype_data_config(self, dataset_id):
        genotype_data_config = \
            super().get_genotype_data_config(dataset_id)
        if genotype_data_config is not None:
            return genotype_data_config
        return self._remote_study_db.get_genotype_data_config(dataset_id)

    def get_common_report(self, common_report_id):
        common_report = \
            super().get_common_report(common_report_id)

        if common_report is not None:
            return common_report

        if common_report_id not in self.remote_study_clients:
            return None

        client = self.remote_study_clients[common_report_id]
        common_report_id = self.remote_study_ids[common_report_id]
        common_report = client.get_common_report(common_report_id)
        return common_report

    def get_common_report_families_data(self, common_report_id):
        families_data = \
            super().get_common_report_families_data(
                common_report_id)
        if families_data:
            for family_data in families_data:
                yield family_data
        else:
            client = self.remote_study_clients[common_report_id]
            common_report_id = self.remote_study_ids[common_report_id]
            response = client.get_common_report_families_data(
                common_report_id)

            for line in response.iter_lines():
                if line:
                    line += "\n".encode("UTF-8")
                    yield line.decode("UTF-8")

    def get_pheno_config(self, study_wrapper):
        logger.warning("WARNING: Using is_remote")
        if not study_wrapper.is_remote:
            dbname = study_wrapper.config.phenotype_data
            return self._pheno_db.config[dbname]

        client = study_wrapper.rest_client
        return client.get_pheno_browser_config(
            study_wrapper.config.phenotype_data)

    def has_pheno_data(self, study_wrapper):
        logger.warning("WARNING: Using is_remote")
        if not study_wrapper.is_remote:
            return study_wrapper.phenotype_data.instruments.keys()

        return "phenotype_data" in study_wrapper.config

    def get_pheno_dbfile(self, study_wrapper):
        config = self.get_pheno_config(study_wrapper)
        return config.browser_dbfile

    def get_pheno_images_url(self, study_wrapper):
        config = self.get_pheno_config(study_wrapper)
        images_dir = get_pheno_browser_images_dir()
        return os.path.join(images_dir, config.name)

    def get_measure_description(self, study_wrapper, measure_id):
        return study_wrapper.phenotype_data.get_measure_description(measure_id)

    def search_measures(self, study_wrapper, instrument, search_term):
        logger.warning("WARNING: Using is_remote")
        if not study_wrapper.is_remote:
            measures = study_wrapper.phenotype_data.search_measures(
                instrument, search_term
            )
            for m in measures:
                yield m
            return

        client = study_wrapper.rest_client
        measures = client.get_browser_measures(
            study_wrapper._remote_study_id,
            instrument,
            search_term
        )
        base = client.build_host_url()
        for m in measures:
            m["measure"]["base_url"] = base
            yield m

    def has_measure(self, study_wrapper, measure_id):
        return study_wrapper.phenotype_data.has_measure(measure_id)

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
            logger.warning(f"Background {background_name} not found!")

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
        builder = self._create_local_enrichment_builder(
            dataset_id, background_name, counting_name, gene_syms)
        if not builder:
            dataset = self.get_wdae_wrapper(dataset_id)
            if dataset.is_remote is False:
                logger.warning("WARNING: Using is_remote")
                logger.warning(
                    "WARNING: Failed to create local enrichment builder!\n"
                    f"dataset: {dataset_id}, "
                    f"requested background: {background_name}, "
                    f"requested counting name: {counting_name}"
                )
            builder = RemoteEnrichmentBuilder(
                dataset, dataset.rest_client,
                background_name, counting_name,
                gene_syms)

        return builder

    @property
    def remote_studies(self):
        return list(self._remote_study_db.get_genotype_data_ids())

    def get_all_denovo_gene_sets(self, types, datasets, collection_id):
        return self.denovo_gene_sets_db.get_all_gene_sets(
            types, datasets, collection_id
        )

    def get_denovo_gene_set(self, gene_set_id, types, datasets, collection_id):
        return self.denovo_gene_sets_db.get_gene_set(
            gene_set_id, types, datasets, collection_id
        )


def get_gpf_instance():
    load_gpf_instance()
    _recreated_dataset_perm()

    return _gpf_instance


def load_gpf_instance():

    global _gpf_instance
    global _gpf_instance_lock

    if _gpf_instance is None:
        _gpf_instance_lock.acquire()
        try:
            if _gpf_instance is None:
                gpf_instance = WGPFInstance(
                    load_eagerly=settings.STUDIES_EAGER_LOADING)  # FIXME
                _gpf_instance = gpf_instance
        finally:
            _gpf_instance_lock.release()

    return _gpf_instance


def reload_datasets(gpf_instance):
    from datasets_api.models import Dataset
    for genotype_data_id in gpf_instance.get_genotype_data_ids():
        # study_wrapper = gpf_instance.get_wdae_wrapper(genotype_data_id)
        Dataset.recreate_dataset_perm(
            genotype_data_id,  # study_wrapper.config.studies
        )

        genotype_data = gpf_instance.get_genotype_data(genotype_data_id)
        if genotype_data is None:
            continue
        if not genotype_data.studies:
            continue

        for study_id in genotype_data.get_studies_ids(leaves=False):
            if study_id is None:
                continue
            Dataset.recreate_dataset_perm(
                study_id,  # study_wrapper.config.studies
            )


def _recreated_dataset_perm():
    global _gpf_instance
    global _gpf_instance_lock
    global _gpf_recreated_dataset_perm

    if _gpf_recreated_dataset_perm:
        return

    _gpf_instance_lock.acquire()
    try:
        assert _gpf_instance is not None

        if not _gpf_recreated_dataset_perm:
            reload_datasets(_gpf_instance)
            _gpf_recreated_dataset_perm = True
    finally:
        _gpf_instance_lock.release()
