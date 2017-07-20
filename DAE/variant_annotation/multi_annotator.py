from .annotator import VariantAnnotator
from .variant import Variant
from .gene_codes import NuclearCode
from .adapters.annovar import AnnovarVariantAnnotation
from .adapters.old import OldVariantAnnotation


class MultiVariantAnnotator:
    def __init__(self, reference_genome, gene_models, code, promoter_len):
        self.reference_genome = reference_genome
        self.gene_models = gene_models
        self.code = code
        self.promoter_len = promoter_len
        self.annotators = [VariantAnnotator(reference_genome, gene_models,
                                            code, promoter_len),
                           OldVariantAnnotation(reference_genome, gene_models,
                                                code, promoter_len),
                           AnnovarVariantAnnotation()]

    def annotate(self, variant):
        return [annotator.annotate(variant) for annotator in self.annotators]

    @classmethod
    def annotate_variant(cls, gm, refG, chr=None, position=None, loc=None,
                         var=None, ref=None, alt=None, length=None, seq=None,
                         typ=None, promoter_len=0):
        annotator = MultiVariantAnnotator(refG, gm, NuclearCode(),
                                          promoter_len)
        variant = Variant(chr, position, loc, var, ref, alt, length, seq, typ)
        return annotator.annotate(variant)
