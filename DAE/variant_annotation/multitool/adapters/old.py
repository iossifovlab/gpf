from .old_VariantAnnotation import annotate_variant, effect_description
from ..simple_effect import SimpleEffect


class OldVariantAnnotation:
    def __init__(self, reference_genome, gene_models, code, promoter_len):
        self.reference_genome = reference_genome
        self.gene_models = gene_models
        self.code = code
        self.promoter_len = promoter_len

    def annotate(self, variant):
        result = annotate_variant(self.gene_models, self.reference_genome,
                                  chr=variant.chromosome,
                                  position=variant.position,
                                  ref=variant.reference, alt=variant.alternate,
                                  promoter_len=self.promoter_len)

        desc = effect_description(result)
        return [SimpleEffect(desc[0], desc[1] + ":" + desc[2])]
