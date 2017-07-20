from ..effect import Effect
import logging


class SpliceSiteEffectChecker:
    def __init__(self, splice_site_length=2):
        self.splice_site_length = splice_site_length
        self.logger = logging.getLogger(__name__)

    @staticmethod
    def clamp(val, min_val, max_val):
        return min(max_val, max(min_val, val))

    def get_related_alternate(self, pos, pos_end, variant):
        last_position = variant.position + len(variant.alternate) - 1

        start_position = max(0, pos - variant.position)
        end_position = pos_end - last_position

        self.logger.debug("Getting:%d-%d from string %s",
                          start_position, end_position + 1,
                          variant.alternate)

        if end_position < 0:
            return variant.alternate[start_position:end_position]
        else:
            return variant.alternate[start_position:]

    def get_mutated_sequence(self, annotator, variant, transcript_model,
                             pos, pos_end):
        length = len(variant.alternate) - len(variant.reference)
        last_position = variant.position + len(variant.alternate) - 1

        mutation_start = self.clamp(variant.position,
                                    pos, pos_end + 1)

        result = annotator.reference_genome.getSequence(
            transcript_model.chr, pos, mutation_start - 1
        )
        self.logger.debug("Prepending:%d-%d from reference genome",
                          pos, mutation_start - 1)

        result += self.get_related_alternate(pos, pos_end, variant)

        self.logger.debug("Middle:%d-%d from mutation data",
                          pos, pos_end)

        mutation_end = self.clamp(last_position + 1,
                                  pos, pos_end + 1)
        result += annotator.reference_genome.getSequence(
            transcript_model.chr, mutation_end - length,
            pos_end - length
        )
        self.logger.debug("Appending:%d-%d from reference genome",
                          mutation_end - length, pos_end - length)

        self.logger.debug("Pos:%d-%d Clamped mutation:%d-%d length:%d",
                          pos, pos_end, mutation_start,
                          mutation_end, length)

        return result

    def are_nucleotides_changed(self, annotator, variant, transcript_model,
                                splice_site_start):
        self.logger.debug("Mutation in splice site detected! Checking if "
                          "nucleotides have changed for pos %d-%d",
                          splice_site_start,
                          splice_site_start + self.splice_site_length - 1)

        seq = annotator.reference_genome.getSequence(
            transcript_model.chr, splice_site_start,
            splice_site_start + self.splice_site_length - 1
        )

        alt = self.get_mutated_sequence(
            annotator, variant, transcript_model, splice_site_start,
            splice_site_start + self.splice_site_length - 1
        )

        self.logger.debug("Nucleotides %s->%s", seq, alt)

        return seq != alt

    def get_effect(self, annotator, variant, transcript_model):
        coding_regions = transcript_model.CDS_regions()
        last_position = variant.position + len(variant.reference)
        prev = None

        for j in coding_regions:
            if prev is None:
                prev = j.stop
                continue

            self.logger.debug("pos: %d-%d checking intronic region %d-%d %d",
                              variant.position, last_position, prev, j.start,
                              j.stop)

            if (variant.position < prev + self.splice_site_length + 1
                    and prev + 1 < last_position):
                worstEffect = "splice-site"
                ef = Effect(worstEffect, transcript_model)
                return ef

            if (variant.position < j.start
                    and j.start - self.splice_site_length < last_position):
                worstEffect = "splice-site"
                ef = Effect(worstEffect, transcript_model)
                return ef
            prev = j.stop
