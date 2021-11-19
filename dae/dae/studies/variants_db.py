import os
import logging
import copy

import toml
from deprecation import deprecated

from dae.studies.study import GenotypeDataStudy, GenotypeDataGroup
from dae.configuration.gpf_config_parser import GPFConfigParser
from dae.configuration.schemas.study_config import study_config_schema


logger = logging.getLogger(__name__)


DEFAULT_STUDY_CONFIG = GPFConfigParser.parse_and_interpolate("""
    [person_set_collections]
    selected_person_set_collections = ["status"]

    status.id = "status"
    status.name = "Affected Status"
    status.domain = [
        {id = "affected", name = "affected", values = ["affected"], color = "#e35252"},
        {id = "unaffected", name = "unaffected", values = ["unaffected"], color = "#ffffff"}
    ]
    status.default = {id = "unspecified", name = "unspecified", values = ["unspecified"], color = "#aaaaaa"}
    status.sources = [{from = "pedigree", source = "status"}]
""", parser=toml.loads)  # noqa


class VariantsDb(object):
    def __init__(
            self,
            dae_config,
            genome,
            gene_models,
            genotype_storage_factory):

        self.dae_config = dae_config

        assert genome is not None
        assert gene_models is not None

        assert genotype_storage_factory is not None

        self.genome = genome
        self.gene_models = gene_models
        self.genotype_storage_factory = genotype_storage_factory

        self._genotype_study_cache = {}
        self._genotype_group_cache = {}
        self.reload()

    def reload(self):
        genotype_study_configs = self._load_study_configs()
        genotype_group_configs = self._load_group_configs()

        overlap = set(genotype_study_configs.keys()) & \
            set(genotype_group_configs.keys())
        if overlap:
            logger.error(
                f"overlapping configurations for studies and groups: "
                f"{overlap}")
            raise ValueError(
                f"overlapping configurations for studies and groups: "
                f"{overlap}")

        self._load_all_genotype_studies(genotype_study_configs)
        self._load_all_genotype_groups(genotype_group_configs)

    def _load_study_configs(self):
        default_config_filename = None
        default_config = None

        if self.dae_config.default_study_config and \
                self.dae_config.default_study_config.conf_file:
            default_config_filename = \
                self.dae_config.default_study_config.conf_file

        if default_config_filename is None or \
                not os.path.exists(default_config_filename):
            logger.warning(
                f"default config file is missing: {default_config_filename}")
            default_config_filename = None

        if default_config_filename is None:
            default_config = copy.deepcopy(DEFAULT_STUDY_CONFIG)

        if self.dae_config.studies is None or \
                self.dae_config.studies.dir is None:
            studies_dir = os.path.join(
                self.dae_config.conf_dir, "studies")
        else:
            studies_dir = self.dae_config.studies.dir

        study_configs = GPFConfigParser.load_directory_configs(
            studies_dir,
            study_config_schema,
            default_config_filename=default_config_filename,
            default_config=default_config
        )

        genotype_study_configs = {}
        for study_config in study_configs:
            assert study_config.id is not None, study_config
            if study_config.enabled is False:
                continue
            genotype_study_configs[study_config.id] = \
                study_config
        return genotype_study_configs

    def _load_group_configs(self):
        default_config_filename = None
        default_config = None

        if self.dae_config.default_study_config and \
                self.dae_config.default_study_config.conf_file:
            default_config_filename = \
                self.dae_config.default_study_config.conf_file

        if default_config_filename is None or \
                not os.path.exists(default_config_filename):
            logger.warning(
                f"default config file is missing: {default_config_filename}")
            default_config_filename = None
        if default_config_filename is None:
            default_config = copy.deepcopy(DEFAULT_STUDY_CONFIG)

        if self.dae_config.datasets is None or \
                self.dae_config.datasets.dir is None:
            datasets_dir = os.path.join(
                self.dae_config.conf_dir, "datasets")
        else:
            datasets_dir = self.dae_config.datasets.dir

        group_configs = GPFConfigParser.load_directory_configs(
            datasets_dir,
            study_config_schema,
            default_config_filename=default_config_filename,
            default_config=default_config
        )

        genotype_group_configs = {}
        for group_config in group_configs:
            assert group_config.id is not None, group_config
            if group_config.enabled is False:
                continue
            genotype_group_configs[group_config.id] = \
                group_config
        return genotype_group_configs

    def get_genotype_study(self, study_id):
        # if study_id not in self._genotype_study_cache:
        #     study_configs = self._load_study_configs()
        #     if study_id not in study_configs:
        #         return None
        #     self._load_genotype_study(study_configs[study_id])
        return self._genotype_study_cache.get(study_id)

    def get_genotype_study_config(self, study_id):
        genotype_study = self.get_genotype_study(study_id)
        if genotype_study is None:
            return None
        return genotype_study.config

    def get_all_genotype_study_ids(self):
        return list(self._genotype_study_cache.keys())

    def get_all_genotype_study_configs(self):
        return [
            genotype_study.config
            for genotype_study in self._genotype_study_cache.values()
        ]

    def get_all_genotype_studies(self):
        return list(self._genotype_study_cache.values())

    def get_genotype_group(self, group_id):
        # if group_id not in self._genotype_group_cache:
        #     group_configs = self._load_group_configs()
        #     if group_id not in group_configs:
        #         return None
        #     self._load_genotype_group(group_configs[group_id])
        return self._genotype_group_cache.get(group_id)

    def get_genotype_group_config(self, group_id):
        genotype_group = self.get_genotype_group(group_id)
        if genotype_group is None:
            return None
        return genotype_group.config

    def get_all_genotype_group_ids(self):
        return list(self._genotype_group_cache.keys())

    def get_all_genotype_groups(self):
        return list(self._genotype_group_cache.values())

    def get_all_genotype_group_configs(self):
        return [
            genotype_group.config
            for genotype_group in self._genotype_group_cache.values()
        ]

    @deprecated(details="start using GPFInstance methods")
    def get_all_ids(self):
        return (
            self.get_all_genotype_study_ids()
            + self.get_all_genotype_group_ids()
        )

    @deprecated(details="start using GPFInstance methods")
    def get_config(self, config_id):
        study_config = self.get_genotype_study_config(config_id)
        genotype_data_group_config = self.get_genotype_group_config(
            config_id
        )
        return study_config if study_config else genotype_data_group_config

    @deprecated(details="start using GPFInstance methods")
    def get(self, object_id):
        genotype_data_study = self.get_genotype_study(object_id)
        genotype_data_group = self.get_genotype_group(object_id)
        return (
            genotype_data_study if genotype_data_study else genotype_data_group
        )

    @deprecated(details="start using GPFInstance methods")
    def get_all_genotype_data(self):
        group_studies = self.get_all_genotype_studies()
        genotype_data_groups = self.get_all_genotype_groups()
        return group_studies + genotype_data_groups

    def _load_all_genotype_studies(self, genotype_study_configs):
        if genotype_study_configs is None:
            genotype_study_configs = self._load_study_configs()

        for study_id, study_config in genotype_study_configs.items():
            if study_id not in self._genotype_study_cache:
                self._load_genotype_study(study_config)

    def _load_genotype_study(self, study_config):
        if not study_config:
            return

        logger.info(
            f"creating genotype group: {study_config.id}")

        genotype_study = self._make_genotype_study(study_config)
        self._genotype_study_cache[study_config.id] = genotype_study
        return genotype_study

    def _make_genotype_study(self, study_config):
        if study_config is None:
            return None

        genotype_storage = self.genotype_storage_factory.get_genotype_storage(
            study_config.genotype_storage.id
        )

        if genotype_storage is None:
            storage_ids = (
                self.genotype_storage_factory.get_genotype_storage_ids()
            )
            logger.error(
                f"unknown genotype storage id: "
                f"{study_config.genotype_storage.id}; "
                f"Known ones: {storage_ids}"
            )
            return None

        try:
            variants = genotype_storage.build_backend(
                study_config, self.genome, self.gene_models
            )

            return GenotypeDataStudy(study_config, variants)
        except Exception as ex:
            logger.error(f"unable to create study {study_config.id}")
            logger.exception(ex)
            return None

    def _load_all_genotype_groups(self, genotype_group_configs=None):
        if genotype_group_configs is None:
            genotype_group_configs = self._load_group_configs()

        for group_id, group_config in genotype_group_configs.items():
            if group_id not in self._genotype_group_cache:
                self._load_genotype_group(group_config)

    def _load_genotype_group(self, group_config):
        if group_config is None:
            return

        logger.info(
            f"creating genotype group: {group_config.id}")
        try:
            group_studies = []
            for child_id in group_config.studies:
                logger.info(f"looking for a child: {child_id}")
                if child_id in self._genotype_study_cache:
                    child_data = self.get_genotype_study(child_id)
                    assert child_data is not None, child_id
                else:
                    child_data = self.get_genotype_group(child_id)
                    if child_data is None:
                        # group not loaded... load it...
                        logger.info(
                            f"child genotype data {child_id} not found; "
                            f"trying to create it...")
                        genotype_group_configs = self._load_group_configs()
                        child_config = genotype_group_configs[child_id]
                        child_data = self._load_genotype_group(child_config)

                group_studies.append(child_data)
            assert group_studies

            genotype_group = GenotypeDataGroup(group_config, group_studies)
            self._genotype_group_cache[group_config.id] = genotype_group
            return genotype_group

        except Exception as ex:
            logger.error(
                f"unable to create genotype data group {group_config.id}")
            logger.exception(ex)

    def register_genotype_data(self, genotype_data):
        if genotype_data.study_id in self.get_all_genotype_study_ids():
            logger.warning(
                f"replacing genotype study instance {genotype_data.study_id}")
        if genotype_data.study_id in self.get_all_genotype_group_ids():
            logger.warning(
                f"replacing genotype group instance {genotype_data.study_id}")

        if genotype_data.is_group:
            self._genotype_group_cache[genotype_data.study_id] = genotype_data
        else:
            self._genotype_study_cache[genotype_data.study_id] = genotype_data
