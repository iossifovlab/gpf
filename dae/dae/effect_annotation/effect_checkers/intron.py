from ..effect import EffectFactory


class IntronicEffectChecker:
    def __init__(self, splice_site_length=2):
        self.splice_site_length = splice_site_length

    def get_effect(self, request):
        coding_regions = request.CDS_regions()
        prev = coding_regions[0].stop

        last_position = request.variant.corrected_ref_position_last

        intron_regions_before_coding = 0
        for j in request.transcript_model.exons:
            if request.transcript_model.cds[0] <= j.stop:
                break
            intron_regions_before_coding += 1

        for i, j in enumerate(coding_regions):
            if prev < request.variant.position and last_position < j.start:
                return EffectFactory.create_intronic_effect(
                    "intron",
                    request,
                    prev,
                    j.start,
                    intron_regions_before_coding + i,
                )
            prev = j.stop
