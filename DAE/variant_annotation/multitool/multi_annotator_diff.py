from ..gene_codes import NuclearCode
from .adapters.annovar import AnnovarVariantAnnotation
from .adapters.old import OldVariantAnnotation
from .adapters.current import CurrentVariantAnnotation
from .adapters.jannovar import JannovarVariantAnnotation


class MultiVariantAnnotatorDiff(object):
    def __init__(self, reference_genome, gene_models,
                 code=NuclearCode(), promoter_len=0):
        self.reference_genome = reference_genome
        self.gene_models = gene_models
        self.code = code
        self.promoter_len = promoter_len

        self.current_annotator = CurrentVariantAnnotation(reference_genome,
                                                          gene_models, code,
                                                          promoter_len)
        self.old_annotator = OldVariantAnnotation(reference_genome,
                                                  gene_models, code,
                                                  promoter_len)
        self.third_party_annotators = [
            AnnovarVariantAnnotation(),
            JannovarVariantAnnotation(reference_genome)
        ]

    @property
    def annotators(self):
        return [self.current_annotator, self.old_annotator] \
            + self.third_party_annotators

    def annotate_variant(self, chr=None, position=None, loc=None, var=None,
                         ref=None, alt=None, length=None, seq=None,
                         typ=None):
        raw_current, effects_current = self.current_annotator.annotate_variant(
            chr, position, loc, var, ref, alt, length, seq, typ
        )

        raw_old, effects_old = self.old_annotator.annotate_variant(
            chr, position, loc, var, ref, alt, length, seq, typ
        )

        raw_current = sorted(raw_current,
                             key=lambda k: k.transcript_id)

        raw_old = sorted(raw_old,
                         key=lambda k: k.transcript_id)

        if len(raw_current) == len(raw_old):
            diff = False
            for effect_left, effect_right in zip(raw_current, raw_old):
                if (effect_left.gene != effect_right.gene or
                    effect_left.transcript_id != effect_right.transcript_id or
                        effect_left.effect != effect_right.effect):
                    diff = True
            if not diff:
                return None

        results = [(self.current_annotator.__class__.__name__,
                    effects_current),
                   (self.old_annotator.__class__.__name__,
                    effects_old)]
        results.extend([(annotator.__class__.__name__,
                         annotator.annotate_variant(chr, position, loc, var,
                                                    ref, alt, length, seq,
                                                    typ)[1])
                        for annotator in self.third_party_annotators])
        return results
