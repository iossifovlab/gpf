import logging

from study_groups.study_group_config import StudyGroupConfig

LOGGER = logging.getLogger(__name__)


class StudyGroup(object):

    def __init__(self, studies, name, phenotype=None):
        self.studies = studies
        self.name = name
        self.phenotype = phenotype

    @staticmethod
    def from_config_file(study_factory, config_file, group_name):
        study_group_configs = StudyGroupConfig.dict_from_config(config_file)

        studies = []
        if group_name not in study_group_configs:
            return None

        study_group_config = study_group_configs[group_name]

        for study_name in study_group_config.studies:
            study = study_factory.get_study(study_name)
            if study is None:
                LOGGER.warning("Unknown study: {}".format(study_name))
                continue
            studies.append(study)

        return StudyGroup(studies, group_name, study_group_config.phenotype)
