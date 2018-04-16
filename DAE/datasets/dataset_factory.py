from datasets.dataset import Dataset
from datasets.dataset_config import DatasetConfig
from variants.annotate_allele_frequencies import VcfAlleleFrequencyAnnotator
from variants.annotate_composite import AnnotatorComposite
from variants.annotate_variant_effects import VcfVariantEffectsAnnotator
from variants.configure import Configure
from variants.raw_vcf import RawFamilyVariants


class DatasetFactory(object):

    def __init__(self, dataset_definition):
        self.dataset_definition = dataset_definition

    @staticmethod
    def make_dataset(name, prefix, _class=Dataset):
        # FIXME: only create these if required (add more arguments?)
        effect_annotator = VcfVariantEffectsAnnotator()
        allele_frequency_annotator = VcfAlleleFrequencyAnnotator()

        composite_annotator = AnnotatorComposite(
            annotators=[effect_annotator, allele_frequency_annotator])

        config = Configure.from_prefix(prefix)

        variants = RawFamilyVariants(config, annotator=composite_annotator)

        return _class(name, variants)

    @staticmethod
    def _build(dataset_config, _class=Dataset):
        assert isinstance(dataset_config, DatasetConfig)

        # TODO: only create these if they are in the config
        effect_annotator = VcfVariantEffectsAnnotator()
        allele_frequency_annotator = VcfAlleleFrequencyAnnotator()
        composite_annotator = AnnotatorComposite(
            annotators=[effect_annotator, allele_frequency_annotator])

        variants_config = Configure.from_prefix(
            dataset_config.variants_prefix)

        variants = RawFamilyVariants(
            variants_config, annotator=composite_annotator)

        return _class(dataset_config.dataset_name, variants)

    def get_dataset(self, dataset_id, _class=Dataset):
        config = self.dataset_definition.get_dataset_config(dataset_id)

        if config:
            return self._build(config, _class)

        return None
