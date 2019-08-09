import logging

from box import Box

from studies.dataset import Dataset
from studies.dataset_config_parser import DatasetConfigParser


LOGGER = logging.getLogger(__name__)


class DatasetFactory(object):

    def __init__(self, study_facade):
        assert study_facade is not None

        self.study_facade = study_facade

    def _get_studies_configs(self, dataset_config):
        studies_configs = []
        for study_id in DatasetConfigParser._split_str_option_list(
                dataset_config[DatasetConfigParser.SECTION].studies):
            study_config = self.study_facade.get_study_config(study_id)
            if study_config:
                studies_configs.append(study_config)
        return studies_configs

    def make_dataset(self, dataset_config):
        assert isinstance(dataset_config, Box), type(dataset_config)

        study_configs = self._get_studies_configs(dataset_config)
        dataset_config = \
            DatasetConfigParser.parse(dataset_config, study_configs)
        if dataset_config is None:
            return None

        studies = []
        for study_id in dataset_config.studies:
            study = self.study_facade.get_study(study_id)

            if not study:
                raise ValueError(
                    "Unknown study: {}, known studies: [{}]".format(
                        dataset_config.studies,
                        ",".join(self.study_facade.get_all_study_ids())
                    ))
            studies.append(study)
        assert studies

        return Dataset(dataset_config, studies)
