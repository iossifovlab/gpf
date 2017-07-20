from ..variant import Variant
from ..gene_codes import NuclearCode
from .adapters.annovar import AnnovarVariantAnnotation
from .adapters.old import OldVariantAnnotation
from .adapters.current import CurrentVariantAnnotation
from .adapters.jannovar import JannovarVariantAnnotation


class MultiVariantAnnotator:
    def __init__(self, reference_genome, gene_models,
                 code=NuclearCode(), promoter_len=0):
        self.reference_genome = reference_genome
        self.gene_models = gene_models
        self.code = code
        self.promoter_len = promoter_len
        self.annotators = [CurrentVariantAnnotation(reference_genome,
                                                    gene_models, code,
                                                    promoter_len),
                           OldVariantAnnotation(reference_genome, gene_models,
                                                code, promoter_len),
                           AnnovarVariantAnnotation(),
                           JannovarVariantAnnotation(reference_genome)]

    def annotate(self, variant):
        return [(annotator.__class__.__name__, annotator.annotate(variant))
                for annotator in self.annotators]

    def annotate_variant(self, chr=None, position=None, loc=None, var=None,
                         ref=None, alt=None, length=None, seq=None,
                         typ=None):
        variant = Variant(chr, position, loc, var, ref, alt, length, seq, typ)
        return self.annotate(variant)
