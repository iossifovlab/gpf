import logging

from datasets.dataset import Dataset
from datasets.dataset_config import DatasetConfig
from studies.study_definition import SingleFileStudiesDefinition
from studies.study_factory import StudyFactory


LOGGER = logging.getLogger(__name__)


class DatasetFactory(object):

    def __init__(self, _class=Dataset, studies_definition=None):
        if studies_definition is None:
            studies_definition = SingleFileStudiesDefinition()

        self._class = _class
        self.studies_factory = StudyFactory()
        self.studies_definition = studies_definition

    def get_dataset(self, dataset_config):
        assert isinstance(dataset_config, DatasetConfig)

        studies = []
        for study_name in dataset_config.studies:
            study_config = self.studies_definition.get_study_config(study_name)
            if study_config:
                studies.append(self.studies_factory.make_study(study_config))
            else:
                LOGGER.warning(
                    "Unknown study: %s, known studies: %s",
                    ",".join(study_name),
                    ",".join(self.studies_definition.get_all_study_names()))

        if not studies:
            raise ValueError(
                "No known studies: [{}]"
                    .format(",".join(dataset_config.studies))
            )

        return self._class(
            dataset_config.dataset_name,
            studies,
            dataset_config.list('preview_columns'),
            dataset_config.list('download_columns')
        )

    @staticmethod
    def with_studies_config(config_file=None, work_dir=None):
        studies_definition = SingleFileStudiesDefinition(config_file, work_dir)

        return DatasetFactory(studies_definition=studies_definition)
