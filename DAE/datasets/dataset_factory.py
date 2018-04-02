from datasets.dataset import Dataset
from variants.annotate_allele_frequencies import VcfAlleleFrequencyAnnotator
from variants.annotate_composite import AnnotatorComposite
from variants.annotate_variant_effects import VcfVariantEffectsAnnotator
from variants.configure import Configure
from variants.raw_vcf import RawFamilyVariants


class DatasetFactory(object):

    @staticmethod
    def make_dataset(name, prefix, _class=Dataset):
        effect_annotator = VcfVariantEffectsAnnotator()
        allele_frequency_annotator = VcfAlleleFrequencyAnnotator()

        composite_annotator = AnnotatorComposite(
            annotators=[effect_annotator, allele_frequency_annotator])

        config = Configure.from_prefix(prefix)

        variants = RawFamilyVariants(config, annotator=composite_annotator)

        return _class(name, variants)
