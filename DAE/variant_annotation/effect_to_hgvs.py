from __future__ import unicode_literals
from builtins import object

import hgvs
import hgvs.location
import hgvs.posedit
import hgvs.edit
import hgvs.sequencevariant
from bioutils.sequences import aa3_to_aa1


class EffectToHGVS(object):

    @classmethod
    def effect_to_HGVS(cls, effect):
        # if effect.effect == "frame-shift":
        #     return cls.handle_frame_shift(effect)
        # else:
        if effect.ref_aa is None or (
                len(effect.ref_aa) == 0 and len(effect.alt_aa) == 0):
            return None

        ref_aa = [
            aa3_to_aa1(aa) if aa != "End" else "*"
            for aa in effect.ref_aa]
        alt_aa = [
            aa3_to_aa1(aa) if aa != "End" else "*"
            for aa in effect.alt_aa]

        if len(ref_aa) > 0:
            start_pos = hgvs.location.AAPosition(
                base=effect.prot_pos, aa=ref_aa[0]
            )
            end_pos = hgvs.location.AAPosition(
                base=effect.prot_pos + len(ref_aa) - 1, aa=ref_aa[-1]
            )
        else:
            assert len(alt_aa) > 0
            start_pos = hgvs.location.AAPosition(
                base=effect.prot_pos, aa=alt_aa[0]
            )
            end_pos = hgvs.location.AAPosition(
                base=effect.prot_pos + len(alt_aa) - 1, aa=alt_aa[-1]
            )

        interval = hgvs.location.Interval(start=start_pos, end=end_pos)

        if len(ref_aa) == 0:
            ref = None
        else:
            ref = "".join(ref_aa)

        if len(alt_aa) == 0:
            alt = None
        else:
            alt = "".join(alt_aa)

        edit = hgvs.edit.AARefAlt(ref=ref, alt=alt)
        posedit = hgvs.posedit.PosEdit(pos=interval, edit=edit)

        return hgvs.sequencevariant.SequenceVariant(
            ac=effect.transcript_id,
            type='p', posedit=posedit)
