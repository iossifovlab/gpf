from studies.study import Study
from variants.raw_thrift import ThriftFamilyVariants
from variants.raw_vcf import RawFamilyVariants


class StudyFactory(object):

    STUDY_TYPES = {
        "vcf": RawFamilyVariants,
        "thrift": ThriftFamilyVariants
    }

    def __init__(self, study_definition):
        self.dataset_definition = study_definition

    def _from_dataset_config(self, study_config):
        from studies.study_config import StudyConfig
        assert isinstance(study_config, StudyConfig)

        if study_config.type not in self.STUDY_TYPES:
            raise ValueError(
                "Unknown study type: {}\nKnown ones: {}"
                .format(study_config.type, list(self.STUDY_TYPES.keys()))
            )

        variants = self.STUDY_TYPES[study_config.type](prefix=study_config.prefix)

        return Study(variants)

    def get_dataset_names(self):
        return self.dataset_definition.dataset_ids

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
