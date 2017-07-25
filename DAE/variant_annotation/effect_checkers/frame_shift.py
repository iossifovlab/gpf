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

    def check_stop_codon(self, request):
        logger = logging.getLogger(__name__)
        last_position = request.variant.position + \
            len(request.variant.reference)

        if request.transcript_model.strand != "+":
            logger.debug("stop codon utr check %d<=%d-%d<=%d",
                         request.transcript_model.cds[0],
                         request.variant.position, last_position,
                         request.transcript_model.cds[0] + 2)

            if (request.variant.position <= request.transcript_model.cds[0] + 2
                    and request.transcript_model.cds[0] <= last_position):

                try:
                    ref_aa, alt_aa = request.get_amino_acids()
                    ref_index = ref_aa.index("End")
                    alt_index = alt_aa.index("End")

                    if ref_index != alt_index:
                        return Effect("no-frame-shift",
                                      request.transcript_model)
                except ValueError:
                    return
                except IndexError:
                    return

        else:
            logger.debug("stop codon utr check %d<=%d-%d<=%d",
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
                        return Effect("no-frame-shift",
                                      request.transcript_model)
                except ValueError:
                    return
                except IndexError:
                    return

    def check_start_codon(self, request):
        logger = logging.getLogger(__name__)
        last_position = request.variant.position + \
            len(request.variant.reference)

        if request.transcript_model.strand == "+":
            logger.debug("start codon frameshift check %d<=%d-%d<=%d",
                         request.transcript_model.cds[0],
                         request.variant.position, last_position,
                         request.transcript_model.cds[0] + 2)

            if (request.variant.position <= request.transcript_model.cds[0] + 2
                    and request.transcript_model.cds[0] <= last_position):
                res = request.find_start_codon()
                if res is None:
                    return

                new_start_codon_offset = res[1]

                old_start_codon_offset = last_position - \
                    request.transcript_model.cds[0]
            else:
                return
        else:
            logger.debug("start codon frameshift check %d<=%d-%d<=%d",
                         request.transcript_model.cds[1] - 2,
                         request.variant.position, last_position,
                         request.transcript_model.cds[1])

            if (request.variant.position <= request.transcript_model.cds[1]
                    and request.transcript_model.cds[1] - 2 <= last_position):
                res = request.find_start_codon()
                if res is None:
                    return

                new_start_codon_offset = res[0]

                old_start_codon_offset = request.transcript_model.cds[1] - 2 \
                    - request.variant.position

            else:
                return

        diff = abs(new_start_codon_offset - old_start_codon_offset)
        logger.debug("new offset=%d old=%d diff=%d", new_start_codon_offset,
                     old_start_codon_offset, diff)

        if diff > 0:
            if diff % 3 == 0:
                ef = Effect("no-frame-shift", request.transcript_model)
            else:
                ef = Effect("frame-shift", request.transcript_model)
            return ef

    def get_effect(self, request):
        logger = logging.getLogger(__name__)

        coding_regions = request.transcript_model.CDS_regions()
        ref_length = len(request.variant.reference)
        alt_length = len(request.variant.alternate)
        length = abs(alt_length - ref_length)

        start_effect = self.check_start_codon(request)
        if start_effect is not None:
            return start_effect

        stop_effect = self.check_stop_codon(request)
        if stop_effect is not None:
            return stop_effect

        for j in coding_regions:
            logger.debug("frameshift check %d<=%d-%d<=%d cds:%d-%d",
                         j.start,
                         request.variant.position,
                         request.variant.ref_position_last,
                         j.stop,
                         request.transcript_model.cds[0],
                         request.transcript_model.cds[1])

            if (request.transcript_model.cds[0] == j.start):
                start = j.start + 3
            else:
                start = j.start
                if (request.variant.position ==
                        request.variant.ref_position_last):
                    start -= 1

            if (request.transcript_model.cds[1] == j.stop):
                stop = j.stop - 3
            else:
                stop = j.stop
                if (request.variant.position ==
                        request.variant.ref_position_last):
                    stop += 1

            if (start <= request.variant.position <= stop):
                logger.debug("inside frameshift %d<=%d-%d<=%d cds:%d-%d m:%s",
                             start,
                             request.variant.position,
                             request.variant.ref_position_last,
                             stop,
                             request.transcript_model.cds[0],
                             request.transcript_model.cds[1])

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
