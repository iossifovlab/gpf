from ..effect import Effect
import logging


class FrameShiftEffectChecker:
    def check_if_new_start(self, request):
        ref_aa, alt_aa = request.get_amino_acids()
        for aa in ref_aa:
            if aa == "End":
                return False
        for aa in alt_aa:
            if aa == "End":
                return True
        return False

    def check_start_codon(self, request):
        logger = logging.getLogger(__name__)
        last_position = request.variant.position + \
            len(request.variant.reference)

        logger.debug("start codon frameshift check %d<=%d-%d<=%d",
                     request.transcript_model.cds[0],
                     request.variant.position, last_position,
                     request.transcript_model.cds[0] + 2)

        if request.transcript_model.strand != "+":
            return

        if (request.variant.position <= request.transcript_model.cds[0] + 2
                and request.transcript_model.cds[0] <= last_position):
            res = request.find_start_codon()
            if res is None:
                return

            new_start_codon_offset = res[1]

            old_start_codon_offset = last_position - \
                request.transcript_model.cds[0]
            logger.debug("new offset=%d old=%d", new_start_codon_offset,
                         old_start_codon_offset)

            diff = new_start_codon_offset - old_start_codon_offset
            if diff > 0:
                if diff % 3 == 0:
                    ef = Effect("no-frame-shift", request.transcript_model)
                else:
                    ef = Effect("frame-shift", request.transcript_model)
                return ef

    def get_effect(self, request):
        coding_regions = request.transcript_model.CDS_regions()
        ref_length = len(request.variant.reference)
        alt_length = len(request.variant.alternate)
        length = abs(alt_length - ref_length)

        start_effect = self.check_start_codon(request)
        if start_effect is not None:
            return start_effect

        for j in coding_regions:
            if (j.start <= request.variant.position <= j.stop
                or
                (request.variant.position == request.variant.ref_position_last
                    and j.start - 1 <= request.variant.position <=
                    j.stop + 1)):
                if length > 0:
                    if length % 3 == 0:
                        if self.check_if_new_start(request):
                            ef = Effect("no-frame-shift-newStop",
                                        request.transcript_model)
                        else:
                            ef = Effect("no-frame-shift",
                                        request.transcript_model)
                    else:
                        ef = Effect("frame-shift", request.transcript_model)
                    ef.prot_pos = 1
                    ef.prot_length = 100
                    return ef
