from ..effect import Effect
import logging


class UTREffectChecker:
    def check_stop_codon(self, request):
        logger = logging.getLogger(__name__)
        last_position = request.variant.position + \
            len(request.variant.reference)

        if request.transcript_model.strand == "+":
            logger.debug("start codon utr check %d<=%d-%d<=%d",
                         request.transcript_model.cds[0],
                         request.variant.position, last_position,
                         request.transcript_model.cds[0] + 2)

            if (request.variant.position <= request.transcript_model.cds[0] + 2
                    and request.transcript_model.cds[0] <= last_position):

                try:
                    ref_aa, alt_aa = request.get_amino_acids()
                    ref_index = len(ref_aa) - ref_aa.index("End")
                    alt_index = len(alt_aa) - alt_aa.index("End")

                    if ref_index != alt_index:
                        return Effect("3'UTR", request.transcript_model)
                except ValueError:
                    return

        else:
            logger.debug("start codon utr check %d<=%d-%d<=%d",
                         request.transcript_model.cds[1] - 2,
                         request.variant.position, last_position,
                         request.transcript_model.cds[1])

            if (request.variant.position <= request.transcript_model.cds[1]
                    and request.transcript_model.cds[1] - 2 <= last_position):

                try:
                    ref_aa, alt_aa = request.get_amino_acids()
                    ref_index = ref_aa.index("End")
                    alt_index = alt_aa.index("End")

                    if ref_index != alt_index:
                        return Effect("3'UTR", request.transcript_model)
                except ValueError:
                    return

    def check_start_codon(self, request):
        logger = logging.getLogger(__name__)
        last_position = request.variant.position + \
            len(request.variant.reference)

        if request.transcript_model.strand == "+":
            logger.debug("start codon utr check %d<=%d-%d<=%d",
                         request.transcript_model.cds[0],
                         request.variant.position, last_position,
                         request.transcript_model.cds[0] + 2)

            if (request.variant.position <= request.transcript_model.cds[0] + 2
                    and request.transcript_model.cds[0] <= last_position):
                res = request.find_start_codon()
                if res is None:
                    return

                new_start_codon_offset = res[0]

                old_start_codon_offset = last_position - \
                    request.transcript_model.cds[0]

                diff = new_start_codon_offset - old_start_codon_offset
                logger.debug("new offset=%d old=%d diff=%d",
                             new_start_codon_offset,
                             old_start_codon_offset, diff)

                if diff > 0:
                    return Effect("5'UTR", request.transcript_model)

        else:
            logger.debug("start codon utr check %d<=%d-%d<=%d",
                         request.transcript_model.cds[1] - 2,
                         request.variant.position, last_position,
                         request.transcript_model.cds[1])

            if (request.variant.position <= request.transcript_model.cds[1]
                    and request.transcript_model.cds[1] - 2 <= last_position):
                res = request.find_start_codon()
                if res is None:
                    return

                new_start_codon_offset = res[1]

                old_start_codon_offset = request.transcript_model.cds[1] - 2 \
                    - request.variant.position

                diff = new_start_codon_offset - old_start_codon_offset
                logger.debug("new offset=%d old=%d diff=%d",
                             new_start_codon_offset,
                             old_start_codon_offset, diff)

                if diff > 0:
                    return Effect("5'UTR", request.transcript_model)

    def get_effect(self, request):
        start_effect = self.check_start_codon(request)
        if start_effect is not None:
            return start_effect

        stop_effect = self.check_stop_codon(request)
        if stop_effect is not None:
            return stop_effect

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
