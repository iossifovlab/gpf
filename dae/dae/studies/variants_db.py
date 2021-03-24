import logging

from deprecation import deprecated

from dae.studies.study import GenotypeDataStudy, GenotypeDataGroup
from dae.configuration.gpf_config_parser import GPFConfigParser
from dae.configuration.schemas.study_config import study_config_schema


logger = logging.getLogger(__name__)


class VariantsDb(object):
    def __init__(
            self,
            dae_config,
            genomes_db,
            genotype_storage_factory):

        self.dae_config = dae_config

        assert genomes_db is not None
        assert genotype_storage_factory is not None

        self.genomes_db = genomes_db
        self.genotype_storage_factory = genotype_storage_factory

        default_config_filename = None
        if (
            dae_config.default_study_config
            and dae_config.default_study_config.conf_file
        ):
            default_config_filename = dae_config.default_study_config.conf_file

        study_configs = GPFConfigParser.load_directory_configs(
            dae_config.studies_db.dir,
            study_config_schema,
            default_config_filename=default_config_filename,
        )
        self.genotype_study_configs = {}
        for study_config in study_configs:
            assert study_config.id is not None, study_config

            self.genotype_study_configs[study_config.id] = \
                study_config

        data_groups = GPFConfigParser.load_directory_configs(
            dae_config.datasets_db.dir,
            study_config_schema,
            default_config_filename=default_config_filename,
        )

        self.genotype_group_configs = {dg.id: dg for dg in data_groups}

        self._filter_disabled()
        self._configuration_check()

        self._genotype_study_cache = {}
        self._genotype_group_cache = {}
        self._load_all_group_studies()
        self._load_all_genotype_groups()

    def _filter_disabled(self):

        to_remove = []
        for k, v in self.genotype_study_configs.items():
            if v.enabled is False:
                to_remove.append(k)
        for disabled_study_id in to_remove:
            logger.debug(f"removing disable study {disabled_study_id}")
            del self.genotype_study_configs[disabled_study_id]
        to_remove.clear()
        for k, v in self.genotype_group_configs.items():
            if v.enabled is False:
                to_remove.append(k)
        for disabled_group_id in to_remove:
            logger.debug(f"removing disable group {disabled_group_id}")
            del self.genotype_group_configs[disabled_group_id]
        logger.debug(
            f"active studies: {list(self.genotype_study_configs.keys())}")
        logger.debug(
            f"active groups: {list(self.genotype_group_configs.keys())}")

    def _configuration_check(self):
        studies_ids = set(self.get_all_genotype_study_ids())
        genotype_data_group_ids = set(self.get_all_genotype_group_ids())

        overlapping = studies_ids.intersection(genotype_data_group_ids)

        assert (
            overlapping == set()
        ), "Overlapping studies and groups ids: {}".format(overlapping)

    def get_genotype_study_config(self, study_id):
        return self.genotype_study_configs.get(study_id)

    def get_genotype_study(self, study_id):
        return self._genotype_study_cache.get(study_id)

    def get_all_genotype_study_ids(self):
        return list(self.genotype_study_configs.keys())

    def get_all_genotype_study_configs(self):
        return [
            genotype_data_study.config
            for genotype_data_study in self._genotype_study_cache.values()
        ]

    def get_all_genotype_studies(self):
        return list(self._genotype_study_cache.values())

    def get_genotype_group_config(self, genotype_data_group_id):
        return self.genotype_group_configs.get(genotype_data_group_id)

    def get_genotype_group(self, genotype_data_group_id):
        return self._genotype_group_cache.get(genotype_data_group_id)

    def get_all_genotype_group_ids(self):
        return list(self.genotype_group_configs.keys())

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

    def _load_all_group_studies(self):
        study_ids = set(self.get_all_genotype_study_ids())
        for study_id in study_ids:
            if study_id not in self._genotype_study_cache:
                self._load_genotype_study(study_id)

    def _load_genotype_study(self, study_id):
        assert study_id not in self._genotype_study_cache

        conf = self.genotype_study_configs.get(study_id)
        if not conf:
            return

        genotype_data_study = self._make_genotype_study(conf)
        if genotype_data_study is None:
            del self.genotype_study_configs[study_id]
            return
        self._genotype_study_cache[study_id] = genotype_data_study
        return genotype_data_study

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
                f"Unknown genotype storage id: "
                f"{study_config.genotype_storage.id}; "
                f"Known ones: {storage_ids}"
            )
            return None

        try:
            variants = genotype_storage.build_backend(
                study_config, self.genomes_db
            )

            return GenotypeDataStudy(study_config, variants)
        except Exception as ex:
            logger.error(f"unable to create study {study_config.id}")
            logger.exception(ex)
            return None

    def _load_all_genotype_groups(self):
        genotype_group_ids = set(self.get_all_genotype_group_ids())
        for group_id in genotype_group_ids:
            if group_id not in self._genotype_group_cache:
                self._load_genotype_group(group_id)

    def _load_genotype_group(self, group_id):
        assert group_id not in self._genotype_study_cache

        group_config = self.genotype_group_configs.get(group_id)
        if group_config is None:
            return

        try:
            group_studies = []
            for child_id in group_config.studies:
                if child_id in self.genotype_study_configs:
                    child_data = self.get_genotype_study(child_id)
                    assert child_data is not None
                else:
                    assert child_id in self.genotype_group_configs
                    child_data = self.get_genotype_group(child_id)

                    if child_data is None:
                        # group not loaded... load it...
                        child_config = self.genotype_group_configs[child_id]
                        child_data = self._load_genotype_group(child_config)

                group_studies.append(child_data)
            assert group_studies

            genotype_group = GenotypeDataGroup(group_config, group_studies)
            self._genotype_group_cache[group_id] = genotype_group
            return genotype_group

        except Exception as ex:
            logger.error(
                f"unable to create genotype data group {group_id}")
            logger.exception(ex)
