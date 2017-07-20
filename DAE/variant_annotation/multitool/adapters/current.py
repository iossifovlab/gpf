from variant_annotation.annotator import VariantAnnotator
from ..simple_effect import SimpleEffect


class CurrentVariantAnnotation(VariantAnnotator):
    def annotate(self, variant):
        result = VariantAnnotator.annotate(self, variant)
        desc = VariantAnnotator.effect_description(result)
        return [SimpleEffect(desc[0], desc[1] + ":" + desc[2])]
