from ..effect import EffectFactory
import logging


class UTREffectChecker:
    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def create_utr_effect(self, request, side):
        if request.transcript_model.strand == side:
            effect_name = "5'UTR"
        else:
            effect_name = "3'UTR"

        ef = EffectFactory.create_effect_with_prot_length(
            effect_name, request
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

    def create_effect(self, request, side):
        coding_regions = request.transcript_model.exons
        last_position = request.variant.position + \
            len(request.variant.reference)
        prev = None

        for i, j in enumerate(coding_regions):
            if (request.variant.position < j.stop
                    and j.start < last_position):
                return self.create_utr_effect(request, side)
            elif (prev is not None
                    and prev <= request.variant.position
                    and last_position < j.start):
                if request.transcript_model.strand == side:
                    effect_name = "5'UTR-intron"
                else:
                    effect_name = "3'UTR-intron"
                return EffectFactory.create_intronic_non_coding_effect(
                    effect_name, request, prev, j.start, i
                )
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

    def get_effect(self, request):
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
            return self.create_effect(request, "+")

        if request.variant.position > request.transcript_model.cds[1]:
            return self.create_effect(request, "-")
