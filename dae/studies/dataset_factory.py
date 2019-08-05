import logging

from dae.studies.dataset import Dataset
from dae.studies.dataset_config import DatasetConfig


LOGGER = logging.getLogger(__name__)


class DatasetFactory(object):

    def __init__(self, study_facade):
        assert study_facade is not None

        self.study_facade = study_facade

    def make_dataset(self, dataset_config):
        assert isinstance(dataset_config, DatasetConfig), type(dataset_config)

        studies = []
        for study_name in dataset_config.studies:
            study = self.study_facade \
                .get_study(study_name)

            if not study:
                raise ValueError(
                    "Unknown study: {}, known studies: [{}]".format(
                        dataset_config.studies,
                        ",".join(self.study_facade.study_all_study_ids())
                    ))
            studies.append(study)
        assert studies

        return Dataset(
            dataset_config,
            studies
        )
