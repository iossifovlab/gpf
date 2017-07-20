from .old_VariantAnnotation import annotate_variant


class OldVariantAnnotation:
    def __init__(self, reference_genome, gene_models, code, promoter_len):
        self.reference_genome = reference_genome
        self.gene_models = gene_models
        self.code = code
        self.promoter_len = promoter_len

    def annotate(self, variant):
        return annotate_variant(self.gene_models, self.reference_genome,
                                chr=variant.chromosome,
                                position=variant.position,
                                ref=variant.reference, alt=variant.alternate,
                                promoter_len=self.promoter_len)
