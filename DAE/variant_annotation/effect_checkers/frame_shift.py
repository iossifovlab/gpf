from ..effect import Effect
import logging


class FrameShiftEffectChecker:
    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def create_effect(self, request, change_length):
        if change_length > 0:
            if change_length % 3 == 0:
                if self.check_if_new_stop(request):
                    ef = Effect("no-frame-shift-newStop",
                                request.transcript_model)
                else:
                    ef = Effect("no-frame-shift",
                                request.transcript_model)
            else:
                ef = Effect("frame-shift", request.transcript_model)
            start_prot, end_prot = request.get_protein_position()
            self.logger.debug("start_prot=%s, end_prot=%s",
                              start_prot, end_prot)
            if start_prot == end_prot:
                ef.prot_pos = start_prot
            else:
                ef.prot_pos = [prot
                               for prot in range(start_prot,
                                                 end_prot + 1)]
            ef.prot_length = request.get_protein_length()

            ref_aa, alt_aa = request.get_amino_acids()
            self.logger.debug("ref aa=%s, alt aa=%s", ref_aa, alt_aa)

            ef.aa_change = "{}->{}".format(
                ",".join(ref_aa),
                ",".join(alt_aa)
            )
            return ef
        return None

    def check_if_new_stop(self, request):
        ref_aa, alt_aa = request.get_amino_acids()
        for aa in ref_aa:
            if aa == "End":
                return False
        for aa in alt_aa:
            if aa == "End":
                return True
        return False

    def check_stop_codon(self, request):
        try:
            ref_aa, alt_aa = request.get_amino_acids()
            if "End" not in ref_aa:
                return None

            ref_index = ref_aa.index("End")
            alt_index = alt_aa.index("End")

            if ref_index != alt_index:
                diff = abs(ref_index - alt_index) * 3
                return self.create_effect(request, diff)
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
            new_start_codon_offset = res[1]

            old_start_codon_offset = request.variant.ref_position_last - \
                request.transcript_model.cds[0]
        else:
            new_start_codon_offset = res[0]

            old_start_codon_offset = request.transcript_model.cds[1] - 2 \
                - request.variant.position

        diff = abs(new_start_codon_offset - old_start_codon_offset)
        self.logger.debug("new offset=%d old=%d diff=%d",
                          new_start_codon_offset,
                          old_start_codon_offset, diff)

        return self.create_effect(request, diff)

    def get_effect(self, request):
        coding_regions = request.CDS_regions()
        ref_length = len(request.variant.reference)
        alt_length = len(request.variant.alternate)
        length = abs(alt_length - ref_length)

        if request.is_start_codon_affected():
            return self.check_start_codon(request)

        if request.is_stop_codon_affected():
            return self.check_stop_codon(request)

        for j in coding_regions:
            start = j.start
            if (request.variant.position ==
                    request.variant.ref_position_last):
                start -= 1
            stop = j.stop
            if (request.variant.position ==
                    request.variant.ref_position_last):
                stop += 1

            self.logger.debug("frameshift %d<=%d<=%d cds:%d-%d exon:%d-%d",
                              start, request.variant.position, stop,
                              request.transcript_model.cds[0],
                              request.transcript_model.cds[1],
                              j.start, j.stop)

            if (start <= request.variant.position <= stop):
                self.logger.debug("fs detected %d<=%d-%d<=%d cds:%d-%d",
                                  start, request.variant.position,
                                  request.variant.ref_position_last, stop,
                                  request.transcript_model.cds[0],
                                  request.transcript_model.cds[1])

                return self.create_effect(request, length)
