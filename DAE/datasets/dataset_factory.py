from datasets.dataset import Dataset
from datasets.dataset_config import DatasetConfig
from variants.annotate_allele_frequencies import VcfAlleleFrequencyAnnotator
from variants.annotate_composite import AnnotatorComposite
from variants.annotate_variant_effects import VcfVariantEffectsAnnotator
from variants.configure import Configure
from variants.raw_vcf import RawFamilyVariants


class DatasetFactory(object):

    def __init__(self, dataset_definition, _class=Dataset):
        self.dataset_definition = dataset_definition
        self._class = _class

    def _from_dataset_config(self, dataset_config):
        assert isinstance(dataset_config, DatasetConfig)

        # TODO: only create these if they are in the config
        effect_annotator = VcfVariantEffectsAnnotator()
        allele_frequency_annotator = VcfAlleleFrequencyAnnotator()
        composite_annotator = AnnotatorComposite(
            annotators=[effect_annotator, allele_frequency_annotator])

        variants_config = Configure.from_prefix_vcf(
            dataset_config.variants_prefix)

        variants = RawFamilyVariants(
            variants_config, annotator=composite_annotator)

        return self._class(
            dataset_config.dataset_name,
            variants,
            dataset_config.list('preview_columns'),
            dataset_config.list('download_columns')
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
