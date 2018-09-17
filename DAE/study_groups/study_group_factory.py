import logging

from studies.study_definition import SingleFileStudiesDefinition
from studies.study_factory import StudyFactory
from study_groups.study_group import StudyGroup
from study_groups.study_group_config import StudyGroupConfig


LOGGER = logging.getLogger(__name__)


class StudyGroupFactory(object):

    def __init__(self, studies_definition=None):
        if studies_definition is None:
            studies_definition = SingleFileStudiesDefinition()

        self.studies_factory = StudyFactory()
        self.studies_definition = studies_definition

    def get_study_group(self, study_group_config):
        assert isinstance(study_group_config, StudyGroupConfig)

        studies = []

        for study_name in study_group_config.studies:
            study_config = self.studies_definition.get_study_config(study_name)
            if study_config:
                studies.append(self.studies_factory.make_study(study_config))
            else:
                LOGGER.warning(
                    "Unknown study: %s, known studies: %s",
                    study_name,
                    ",".join(self.studies_definition.get_all_study_names()))

        if not studies:
            raise ValueError(
                "No known studies: [{}]".format(
                    ",".join(study_group_config.studies))
            )

        return StudyGroup(
            study_group_config.name,
            studies
        )

    def get_study_configs(self, study_group_config):
        study_configs = []

        for study_name in study_group_config.studies:
            study_configs.append(
                self.studies_definition.get_study_config(study_name))

        return study_configs
