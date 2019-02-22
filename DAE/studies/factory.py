
from studies.study_definition import DirectoryEnabledStudiesDefinition
from studies.study_factory import StudyFactory
from studies.study_facade import StudyFacade


class VariantsDb(object):

    def __init__(self, dae_config, thrift_connection=None):
        self.dae_config = dae_config

        self.studies_definitions = DirectoryEnabledStudiesDefinition(
            studies_dir=dae_config.studies_dir,
            work_dir=dae_config.dae_data_dir)

        study_factory = StudyFactory(thrift_connection)

        self.study_facade = StudyFacade(
            self.studies_definitions, study_factory)

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
