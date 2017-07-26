from ..effect import Effect
import logging


class UTREffectChecker:
    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def check_stop_codon(self, request):
        if not request.has_3_UTR_region():
            return

        try:
            ref_aa, alt_aa = request.get_amino_acids()
            if "End" not in ref_aa:
                return None

            ref_index = ref_aa.index("End")
            alt_index = alt_aa.index("End")

            if ref_index == alt_index:
                return Effect("3'UTR", request.transcript_model)
        except ValueError:
            pass
        except IndexError:
            pass
        return None

    def check_start_codon(self, request):
        res = request.find_start_codon()
        if res is None:
            return None

        if request.transcript_model.strand == "+":
            new_start_codon_offset = res[0]

            old_start_codon_offset = request.variant.ref_position_last - \
                request.transcript_model.cds[0]
        else:
            new_start_codon_offset = res[1]

            old_start_codon_offset = request.transcript_model.cds[1] - 2 \
                - request.variant.position

        diff = abs(new_start_codon_offset - old_start_codon_offset)
        self.logger.debug("new offset=%d old=%d diff=%d",
                          new_start_codon_offset,
                          old_start_codon_offset, diff)

        if diff > 0:
            return Effect("5'UTR", request.transcript_model)
        return None

    def get_effect(self, request):
        if request.is_start_codon_affected():
            return self.check_start_codon(request)

        if request.is_stop_codon_affected():
            return self.check_stop_codon(request)

        self.logger.debug("utr check: %d<%d or %d>%d exons:%d-%d",
                          request.variant.position,
                          request.transcript_model.cds[0],
                          request.variant.position,
                          request.transcript_model.cds[1],
                          request.transcript_model.exons[0].start,
                          request.transcript_model.exons[-1].stop)

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
