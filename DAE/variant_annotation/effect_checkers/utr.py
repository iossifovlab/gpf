from ..effect import Effect
import logging


class UTREffectChecker:
    def get_effect(self, annotator, variant, transcript_model):
        logger = logging.getLogger(__name__)
        logger.debug("is coding=%s", transcript_model.is_coding())
        if not transcript_model.is_coding():
            all_regs = transcript_model.all_regions()
            last_pos = variant.position + len(variant.reference)
            for r in all_regs:
                if (variant.position <= r.stop
                        and r.start < last_pos):
                    return Effect("non-coding", transcript_model)

            return Effect("non-coding-intron", transcript_model)

        if variant.position < transcript_model.cds[0]:
            if transcript_model._TranscriptModel__check_if_exon(
                variant.position, variant.position_last
            ):
                if transcript_model.strand == "+":
                    return Effect("5'UTR", transcript_model)
                return Effect("3'UTR", transcript_model)

            if transcript_model.strand == "+":
                return Effect("5'UTR-intron", transcript_model)
            return Effect("3'UTR-intron", transcript_model)

        if variant.position > transcript_model.cds[1]:
            if transcript_model._TranscriptModel__check_if_exon(
                variant.position, variant.position_last
            ):
                if transcript_model.strand == "+":
                    return Effect("3'UTR", transcript_model)
                return Effect("5'UTR", transcript_model)

            if transcript_model.strand == "+":
                return Effect("3'UTR-intron", transcript_model)
            return Effect("5'UTR-intron", transcript_model)
