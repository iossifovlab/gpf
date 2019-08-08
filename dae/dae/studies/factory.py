from dae.pheno.pheno_factory import PhenoFactory
from dae.studies.study_definition import DirectoryEnabledStudiesDefinition
from dae.studies.study_factory import StudyFactory
from dae.studies.study_facade import StudyFacade
from dae.studies.dataset_definition import DirectoryEnabledDatasetsDefinition
from dae.studies.dataset_factory import DatasetFactory
from dae.studies.dataset_facade import DatasetFacade


class VariantsDb(object):

    def __init__(
            self, dae_config,
            pheno_factory=None, thrift_connection=None):
        self.dae_config = dae_config
        self.studies_definitions = DirectoryEnabledStudiesDefinition(
            studies_dir=dae_config.studies_dir,
            work_dir=dae_config.dae_data_dir,
            default_conf=dae_config.default_configuration_conf)

        study_factory = StudyFactory(dae_config, thrift_connection)

        if pheno_factory is None:
            pheno_factory = PhenoFactory(dae_config=dae_config)
        self.pheno_factory = pheno_factory

        self.study_facade = StudyFacade(
            self.dae_config,
            self.pheno_factory, self.studies_definitions, study_factory)

        self.datasets_definitions = DirectoryEnabledDatasetsDefinition(
            self.study_facade,
            datasets_dir=dae_config.datasets_dir,
            work_dir=dae_config.dae_data_dir,
            default_conf=dae_config.default_configuration_conf)
        self.dataset_factory = DatasetFactory(
            self.study_facade)
        self.dataset_facade = DatasetFacade(
            self.datasets_definitions, self.dataset_factory,
            self.pheno_factory)

        self._configuration_check()

    def _configuration_check(self):
        studies_ids = set(self.get_studies_ids())
        dataset_ids = set(self.get_datasets_ids())

        overlapping = studies_ids.intersection(dataset_ids)

        assert overlapping == set(), \
            "Overlapping studies and datasets ids: {}".format(overlapping)

    def get_studies_ids(self):
        return self.studies_definitions.study_ids

    def get_study_config(self, study_id):
        return self.study_facade.get_study_config(study_id)

    def get_study(self, study_id):
        return self.study_facade.get_study(study_id)

    def get_study_wdae_wrapper(self, study_id):
        return self.study_facade.get_study_wdae_wrapper(study_id)

    def get_all_studies(self):
        return self.study_facade.get_all_studies()

    def get_all_studies_wrapper(self):
        return self.study_facade.get_all_studies_wrapper()

    def get_all_study_configs(self):
        return self.study_facade.get_all_study_configs()

    def get_datasets_ids(self):
        return self.datasets_definitions.dataset_ids

    # def get_datasets_names(self):
    #     return self.datasets_definitions.get_all_dataset_names()

    def get_dataset_config(self, dataset_id):
        return self.dataset_facade.get_dataset_config(dataset_id)

    def get_dataset(self, dataset_id):
        return self.dataset_facade.get_dataset(dataset_id)

    def get_dataset_wdae_wrapper(self, dataset_id):
        return self.dataset_facade.get_dataset_wdae_wrapper(dataset_id)

    def get_all_datasets(self):
        return self.dataset_facade.get_all_datasets()

    def get_all_datasets_wrapper(self):
        return self.dataset_facade.get_all_datasets_wrapper()

    def get_all_dataset_configs(self):
        return self.dataset_facade.get_all_dataset_configs()

    def get_all_ids(self):
        return self.get_studies_ids() + self.get_datasets_ids()

    # def get_all_names(self):
    #     return self.get_studies_names() + self.get_datasets_names()

    def get_config(self, id):
        study_config = self.get_study_config(id)
        dataset_config = self.get_dataset_config(id)
        return study_config if study_config else dataset_config

    def get(self, id):
        study = self.get_study(id)
        dataset = self.get_dataset(id)
        return study if study else dataset

    def get_wdae_wrapper(self, id):
        study_wdae_wrapper = self.get_study_wdae_wrapper(id)
        dataset_wdae_wrapper = self.get_dataset_wdae_wrapper(id)
        return study_wdae_wrapper\
            if study_wdae_wrapper else dataset_wdae_wrapper

    def get_all_configs(self):
        study_configs = self.get_all_study_configs()
        dataset_configs = self.get_all_dataset_configs()
        return study_configs + dataset_configs

    def get_all(self):
        studies = self.get_all_studies()
        datasets = self.get_all_datasets()
        return studies + datasets

    def get_all_wrappers(self):
        study_wrappers = self.get_all_studies_wrapper()
        dataset_wrappers = self.get_all_datasets_wrapper()
        return study_wrappers + dataset_wrappers
