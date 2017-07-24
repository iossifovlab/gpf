from ..effect import Effect
import logging


class UTREffectChecker:
    def get_effect(self, request):
        logger = logging.getLogger(__name__)
        logger.debug("utr check: %d<%d or %d>%d",
                     request.variant.position,
                     request.transcript_model.cds[0],
                     request.variant.position,
                     request.transcript_model.cds[1])

        if request.variant.position < request.transcript_model.cds[0]:
            if request.transcript_model._TranscriptModel__check_if_exon(
                request.variant.position, request.variant.ref_position_last
            ):
                if request.transcript_model.strand == "+":
                    return Effect("5'UTR", request.transcript_model)
                return Effect("3'UTR", request.transcript_model)

            if request.transcript_model.strand == "+":
                return Effect("5'UTR-intron", request.transcript_model)
            return Effect("3'UTR-intron", request.transcript_model)

        if request.variant.position > request.transcript_model.cds[1]:
            if request.transcript_model._TranscriptModel__check_if_exon(
                request.variant.position, request.variant.ref_position_last
            ):
                if request.transcript_model.strand == "+":
                    return Effect("3'UTR", request.transcript_model)
                return Effect("5'UTR", request.transcript_model)

            if request.transcript_model.strand == "+":
                return Effect("3'UTR-intron", request.transcript_model)
            return Effect("5'UTR-intron", request.transcript_model)
