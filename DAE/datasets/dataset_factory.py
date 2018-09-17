import logging

from datasets.dataset import Dataset
from datasets.dataset_config import DatasetConfig
from study_groups.study_group_definition import SingleFileStudiesGroupDefinition
from study_groups.study_group_factory import StudyGroupFactory


LOGGER = logging.getLogger(__name__)


class DatasetFactory(object):

    def __init__(
            self, _class=Dataset, study_definition=None,
            study_group_definition=None):
        if study_group_definition is None:
            study_group_definition = SingleFileStudiesGroupDefinition()

        studies_factory = StudyGroupFactory(
            studies_definition=study_definition)

        self._class = _class
        self.study_group_factory = studies_factory
        self.study_group_definition = study_group_definition

    def get_dataset(self, dataset_config):
        assert isinstance(dataset_config, DatasetConfig)

        study_group_config = self.study_group_definition \
            .get_study_group_config(dataset_config.study_group)

        if not study_group_config:
            raise ValueError(
                "Unknown study group: {}, known study groups: [{}]".format(
                    dataset_config.study_group,
                    ",".join(self.study_group_definition.study_group_ids()))
            )

        study_group =\
            self.study_group_factory.get_study_group(study_group_config)

        return self._class(
            dataset_config.dataset_name,
            study_group,
            dataset_config
        )

    def get_study_group_factory(self):
        return self.study_group_factory

    def get_study_group_definition(self):
        return self.study_group_definition
