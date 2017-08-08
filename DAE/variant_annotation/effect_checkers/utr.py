from ..effect import EffectFactory
from intronic_base import IntronicBase
import logging


class UTREffectChecker(IntronicBase):
    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def create_utr_effect(self, request, side):
        coding_regions = request.transcript_model.exons
        last_position = request.variant.position + \
            len(request.variant.reference)
        prev = None

        for i, j in enumerate(coding_regions):
            if (request.variant.position < j.stop
                    and j.start < last_position):
                if request.transcript_model.strand == side:
                    ef = EffectFactory.create_effect_with_prot_length(
                        "5'UTR", request
                    )
                else:
                    ef = EffectFactory.create_effect_with_prot_length(
                        "3'UTR", request
                    )

                self.logger.debug("pos=%d cds end=%d",
                                  request.variant.ref_position_last - 1,
                                  request.transcript_model.cds[0])

                if side == "+":
                    ef.dist_from_coding = request.get_exonic_distance(
                        max(request.variant.position,
                            request.variant.ref_position_last - 1),
                        request.transcript_model.cds[0]
                    )
                else:
                    ef.dist_from_coding = request.get_exonic_distance(
                        request.transcript_model.cds[1],
                        request.variant.position
                    )
                return ef
            elif (prev is not None
                    and prev <= request.variant.position
                    and last_position < j.start):
                if request.transcript_model.strand == side:
                    return self.create_effect("5'UTR-intron", request, prev,
                                              j.start, i)
                return self.create_effect("3'UTR-intron", request, prev,
                                          j.start, i)
            prev = j.stop

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
                ef = EffectFactory.create_effect_with_prot_length("3'UTR",
                                                                  request)
                ef.dist_from_coding = 0
                return ef
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
            ef = EffectFactory.create_effect_with_prot_length("5'UTR", request)
            ef.dist_from_coding = 0
            return ef
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
            return self.create_utr_effect(request, "+")

        if request.variant.position > request.transcript_model.cds[1]:
            return self.create_utr_effect(request, "-")
