from studies.study import Study
from studies.study_config import StudyConfig


class StudyFactory(object):

    def __init__(self, study_definition):
        self.dataset_definition = study_definition

    def _from_dataset_config(self, study_config):
        assert isinstance(study_config, StudyConfig)

        variants_config = Configure.from_prefix_vcf(
            study_config.variants_prefix)

        variants = RawFamilyVariants(
            variants_config, annotator=composite_annotator)

        return Study(
            study_config.dataset_name,
            variants
        )

    def get_dataset_names(self):
        return self.dataset_definition.dataset_ids()

    def get_dataset(self, dataset_id):
        config = self.dataset_definition.get_dataset_config(dataset_id)

        if config:
            return self._from_dataset_config(config)

        return None

    def get_all_datasets(self):
        return [
            self._from_dataset_config(config)
            for config in self.dataset_definition.get_all_dataset_configs()
        ]

    def get_dataset_description(self, dataset_id):
        config = self.dataset_definition.get_dataset_config(dataset_id)

        if config:
            return config.get_dataset_description()

        return None

    def get_dataset_descriptions(self):
        return filter(lambda c: c is not None, [
            config.get_dataset_description()
            for config in self.dataset_definition.get_all_dataset_configs()
        ])
