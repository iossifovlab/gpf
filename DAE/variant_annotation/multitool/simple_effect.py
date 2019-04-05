from __future__ import unicode_literals
from builtins import object


class Effect(object):
    gene = None
    transcript_id = None
    strand = None
    effect = None
    prot_pos = None
    non_coding_pos = None
    prot_length = None
    length = None
    which_intron = None
    how_many_introns = None
    side = None
    dist_from_coding = None
    splice_site = None
    aa_change = None
    splice_site_context = None
    cnv_type = None
    dist_from_5utr = None

    def __init__(self, effect_name, transcript_model=None):
        self.effect = effect_name
        if transcript_model is not None:
            self.gene = transcript_model.gene
            self.strand = transcript_model.strand
            self.transcript_id = transcript_model.trID

    def __repr__(self):
        return "Effect gene:{} trID:{} strand:{} effect:{} " \
            "protein pos:{}/{} aa: {}".format(
                self.gene, self.transcript_id, self.strand, self.effect,
                self.prot_pos, self.prot_length, self.aa_change)


class SimpleEffect(object):
    def __init__(self, effect_type, effect_details):
        self.effect_type = effect_type
        self.effect_details = effect_details
