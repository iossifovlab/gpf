from variant_annotation.annotator import VariantAnnotator
from ..simple_effect import SimpleEffect
from .base import BaseAdapter


class CurrentVariantAnnotation(BaseAdapter):
    def __init__(self, reference_genome, gene_models, code, promoter_len):
        self.annotator = VariantAnnotator(reference_genome, gene_models, code,
                                          promoter_len)

    def annotate(self, variant):
        result = self.annotator.annotate(variant)
        desc = self.annotator.effect_description(result)
        return result, [SimpleEffect(desc[0], desc[1] + ":" + desc[2])]
