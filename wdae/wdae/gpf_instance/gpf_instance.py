import json
import logging
from django.conf import settings

from threading import Lock

from dae.gpf_instance.gpf_instance import GPFInstance
from studies.study_wrapper import StudyWrapper, RemoteStudyWrapper

from remote.rest_api_client import RESTClient, RESTClientRequestError

from dae.enrichment_tool.tool import EnrichmentTool
from dae.enrichment_tool.event_counters import CounterBase
from enrichment_api.enrichment_builder import \
    EnrichmentBuilder, RemoteEnrichmentBuilder

from requests.exceptions import ConnectionError


logger = logging.getLogger(__name__)
__all__ = ["get_gpf_instance"]


_gpf_instance = None
_gpf_recreated_dataset_perm = False
_gpf_instance_lock = Lock()


class WGPFInstance(GPFInstance):
    def __init__(self, *args, **kwargs):
        super(WGPFInstance, self).__init__(*args, **kwargs)
        self._remote_study_clients = dict()
        self._remote_study_ids = dict()
        self._study_wrappers = dict()

        if getattr(settings, "REMOTES", None):
            for remote in settings.REMOTES:
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
                    self._fetch_remote_studies(client)
                except ConnectionError as err:
                    logger.error(err)
                    logger.error(f"Failed to create remote {remote['id']}")
                except RESTClientRequestError as err:
                    logger.error(err.message)

    def _fetch_remote_studies(self, rest_client):
        studies = rest_client.get_datasets()
        for study in studies["data"]:
            logger.info(f"creating remote genotype data: {study['id']}")
            study_wrapper = RemoteStudyWrapper(study["id"], rest_client)
            study_id = study_wrapper.study_id
            self._remote_study_ids[study_id] = study["id"]
            self._remote_study_clients[study_id] = rest_client
            self._study_wrappers[study_id] = study_wrapper

    def register_genotype_data(self, genotype_data):
        super(WGPFInstance, self).register_genotype_data(genotype_data)

        logger.debug(f"genotype data config; {genotype_data.id}")

        study_wrapper = StudyWrapper(
            genotype_data,
            self._pheno_db,
            self.gene_weights_db
        )
        return study_wrapper

    def make_wdae_wrapper(self, dataset_id):
        genotype_data = self.get_dataset(dataset_id)
        if genotype_data is None:
            return None

        study_wrapper = StudyWrapper(
            genotype_data,
            self._pheno_db,
            self.gene_weights_db
        )
        return study_wrapper

    def get_wdae_wrapper(self, dataset_id):
        if dataset_id not in self._study_wrappers.keys():
            wrapper = self.make_wdae_wrapper(dataset_id)
            if wrapper is not None:
                self._study_wrappers[dataset_id] = wrapper
        else:
            wrapper = self._study_wrappers.get(dataset_id, None)
        return wrapper

    def get_genotype_data_ids(self):
        return (
            list(super(WGPFInstance, self).get_genotype_data_ids())
            + self.remote_studies
        )

    def get_genotype_data(self, dataset_id):
        # TODO: Avoid returning different types of data when remote
        # Returns an instance GenotypeData when local, a Box config when remote
        genotype_data = super(WGPFInstance, self).get_genotype_data(dataset_id)
        if genotype_data is not None:
            return genotype_data

        wrapper = self.get_wdae_wrapper(dataset_id)

        if wrapper is None:
            return None

        genotype_data = wrapper.config
        return genotype_data

    def get_genotype_data_config(self, dataset_id):
        genotype_data = \
            super(WGPFInstance, self).get_genotype_data_config(dataset_id)
        if genotype_data is not None:
            return genotype_data
        genotype_data = self.get_genotype_data(dataset_id)
        return genotype_data

    def get_common_report(self, common_report_id):
        common_report = \
            super(WGPFInstance, self).get_common_report(common_report_id)

        if common_report is not None:
            return common_report

        if common_report_id not in self._remote_study_clients:
            return None

        client = self._remote_study_clients[common_report_id]
        common_report_id = self._remote_study_ids[common_report_id]
        common_report = client.get_common_report(common_report_id)
        return common_report

    def get_common_report_families_data(self, common_report_id):
        families_data = \
            super(WGPFInstance, self).get_common_report_families_data(
                common_report_id)
        if families_data:
            for family_data in families_data:
                yield family_data
        else:
            client = self._remote_study_clients[common_report_id]
            common_report_id = self._remote_study_ids[common_report_id]
            response = client.get_common_report_families_data(
                common_report_id)

            for line in response.iter_lines():
                if line:
                    line += "\n".encode("UTF-8")
                    yield line.decode("UTF-8")

    def get_pheno_config(self, study_wrapper):
        logger.warning("WARNING: Using is_remote")
        if not study_wrapper.is_remote:
            return super(WGPFInstance, self).get_pheno_config(study_wrapper)

        client = study_wrapper.rest_client
        return client.get_pheno_browser_config(
            study_wrapper.config.phenotype_data)

    def has_pheno_data(self, study_wrapper):
        logger.warning("WARNING: Using is_remote")
        if not study_wrapper.is_remote:
            return super(WGPFInstance, self).has_pheno_data(study_wrapper)

        return "phenotype_data" in study_wrapper.config

    def get_measure_description(self, study_wrapper, measure_id):
        logger.warning("WARNING: Using is_remote")
        if not study_wrapper.is_remote:
            return super(WGPFInstance, self).get_measure_description(
                study_wrapper, measure_id)

        return study_wrapper.phenotype_data.get_measure_description(measure_id)

    def get_instruments(self, study_wrapper):
        logger.warning("WARNING: Using is_remote")
        if not study_wrapper.is_remote:
            return super(WGPFInstance, self).get_instruments(study_wrapper)

        return study_wrapper.rest_client.get_instruments(
            study_wrapper._remote_study_id)

    def get_regressions(self, study_wrapper):
        logger.warning("WARNING: Using is_remote")
        if not study_wrapper.is_remote:
            return super(WGPFInstance, self).get_regressions(study_wrapper)

        return study_wrapper.rest_client.get_regressions(
            study_wrapper._remote_study_id)

    def get_measures_info(self, study_wrapper):
        logger.warning("WARNING: Using is_remote")
        if not study_wrapper.is_remote:
            return super(WGPFInstance, self).get_measures_info(study_wrapper)

        client = study_wrapper.rest_client
        return client.get_browser_measures_info(study_wrapper._remote_study_id)

    def search_measures(self, study_wrapper, instrument, search_term):
        logger.warning("WARNING: Using is_remote")
        if not study_wrapper.is_remote:
            measures = super(WGPFInstance, self).search_measures(
                study_wrapper, instrument, search_term)
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

    def get_study_enrichment_config(self, dataset_id):
        result = \
            super(WGPFInstance, self).get_study_enrichment_config(dataset_id)

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
            builder = RemoteEnrichmentBuilder(
                dataset, dataset.rest_client,
                background_name, counting_name,
                gene_syms)

        return builder

    @property
    def remote_studies(self):
        return list(self._remote_study_clients.keys())


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
