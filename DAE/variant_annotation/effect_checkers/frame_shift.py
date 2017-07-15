from ..effect import Effect


class FrameShiftEffectChecker:
    def get_effect(self, annotator, variant, transcript_model):
        coding_regions = transcript_model.CDS_regions()
        ref_length = len(variant.reference)
        alt_length = len(variant.alternate)
        length = abs(alt_length - ref_length)

        for j in coding_regions:
            if (j.start <= variant.position <= j.stop):
                if length > 0:
                    if length % 3 == 0:
                        ef = Effect("no-frame-shift", transcript_model)

                    else:
                        ef = Effect("frame-shift", transcript_model)
                    ef.prot_pos = 1
                    ef.prot_length = 100
                    return ef
