
from studies.study_definition import DirectoryEnabledStudiesDefinition
from studies.study_factory import StudyFactory
from studies.study_facade import StudyFacade
from studies.dataset_definition import DirectoryEnabledDatasetsDefinition
from studies.dataset_factory import DatasetFactory
from studies.dataset_facade import DatasetFacade

from common_reports.common_report import CommonReportsGenerator
from common_reports.common_report_facade import CommonReportFacade
from common_reports.config import CommonReportsQueryObjects

from gene.scores import ScoreLoader


class VariantsDb(object):

    def __init__(self, dae_config, thrift_connection=None):
        self.dae_config = dae_config

        self.studies_definitions = DirectoryEnabledStudiesDefinition(
            studies_dir=dae_config.studies_dir,
            work_dir=dae_config.dae_data_dir,
            default_conf=dae_config.default_configuration_conf)

        study_factory = StudyFactory(thrift_connection)

        self.study_facade = StudyFacade(
            self.studies_definitions, study_factory)

        self.datasets_definitions = DirectoryEnabledDatasetsDefinition(
            self.study_facade,
            datasets_dir=dae_config.datasets_dir,
            work_dir=dae_config.dae_data_dir,
            default_conf=dae_config.default_configuration_conf)
        self.dataset_factory = DatasetFactory(study_facade=self.study_facade)
        self.dataset_facade = DatasetFacade(
            self.datasets_definitions, self.dataset_factory)

        self.common_reports_query_objects = CommonReportsQueryObjects(
            self.study_facade, self.dataset_facade)
        self.common_reports_generator = CommonReportsGenerator(
            self.common_reports_query_objects)
        self.common_report_facade = CommonReportFacade(
            self.common_reports_query_objects)

        self.score_loader = ScoreLoader()

    def get_studies_ids(self):
        return self.studies_definitions.study_ids

    def get_studies_names(self):
        return self.studies_definitions.get_all_study_names()

    def get_study_config(self, study_id):
        return self.studies_definitions.get_study_config(study_id)

    def get_study(self, study_id):
        return self.study_facade.get_study(study_id)

    def get_study_wdae_wrapper(self, study_id):
        return self.study_facade.get_study_wdae_wrapper(study_id)

    def get_datasets_ids(self):
        return self.datasets_definitions.dataset_ids

    def get_datasets_names(self):
        return self.datasets_definitions.get_all_dataset_names()

    def get_dataset_config(self, dataset_id):
        return self.datasets_definitions.get_dataset_config(dataset_id)

    def get_dataset(self, dataset_id):
        return self.dataset_facade.get_dataset(dataset_id)

    def get_dataset_wdae_wrapper(self, dataset_id):
        return self.dataset_facade.get_dataset_wdae_wrapper(dataset_id)
