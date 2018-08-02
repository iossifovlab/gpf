from datasets.dataset import Dataset
from datasets.dataset_config import DatasetConfig
from variants.annotate_allele_frequencies import VcfAlleleFrequencyAnnotator
from variants.annotate_composite import AnnotatorComposite
from variants.annotate_variant_effects import VcfVariantEffectsAnnotator
from variants.configure import Configure
from variants.raw_vcf import RawFamilyVariants


class DatasetFactory(object):

    def __init__(self, _class=Dataset):
        self._class = _class

    def get_dataset(self, dataset_config):
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
