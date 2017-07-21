from ..effect import Effect
import logging


class UTREffectChecker:
    def get_effect(self, request):
        logger = logging.getLogger(__name__)
        logger.debug("is coding=%s", request.transcript_model.is_coding())
        if not request.transcript_model.is_coding():
            all_regs = request.transcript_model.all_regions()
            last_pos = request.variant.position + \
                len(request.variant.reference)
            for r in all_regs:
                if (request.variant.position <= r.stop
                        and r.start < last_pos):
                    return Effect("non-coding", request.transcript_model)

            return Effect("non-coding-intron", request.transcript_model)

        if request.variant.position < request.transcript_model.cds[0]:
            if request.transcript_model._TranscriptModel__check_if_exon(
                request.variant.position, request.variant.position_last
            ):
                if request.transcript_model.strand == "+":
                    return Effect("5'UTR", request.transcript_model)
                return Effect("3'UTR", request.transcript_model)

            if request.transcript_model.strand == "+":
                return Effect("5'UTR-intron", request.transcript_model)
            return Effect("3'UTR-intron", request.transcript_model)

        if request.variant.position > request.transcript_model.cds[1]:
            if request.transcript_model._TranscriptModel__check_if_exon(
                request.variant.position, request.variant.position_last
            ):
                if request.transcript_model.strand == "+":
                    return Effect("3'UTR", request.transcript_model)
                return Effect("5'UTR", request.transcript_model)

            if request.transcript_model.strand == "+":
                return Effect("3'UTR-intron", request.transcript_model)
            return Effect("5'UTR-intron", request.transcript_model)
