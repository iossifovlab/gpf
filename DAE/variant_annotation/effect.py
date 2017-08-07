class Effect:
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
    dist_from_acceptor = None
    dist_from_donor = None
    intron_length = None

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

    def create_effect_details(self):
        if self.effect in ["intron", "5'UTR-intron", "3'UTR-intron",
                           "non-coding-intron"]:
            eff_d = str(self.which_intron) + "/" + str(self.how_many_introns)
            eff_d += "[" + str(self.dist_from_coding) + "]"
        elif (self.effect == "frame-shift" or self.effect == "no-frame-shift"
              or self.effect == "no-frame-shift-newStop"):
            eff_d = str(self.prot_pos) + "/" + str(self.prot_length)
            eff_d += "(" + self.aa_change + ")"
        elif self.effect == "splice-site" or self.effect == "synonymous":
            eff_d = str(self.prot_pos) + "/" + str(self.prot_length)
        elif self.effect == "5'UTR" or self.effect == "3'UTR":
            eff_d = str(self.dist_from_coding)
        elif self.effect in ["non-coding", "unknown", "tRNA:ANTICODON"]:
            eff_d = str(self.length)
        elif self.effect == "noStart" or self.effect == "noEnd":
            eff_d = str(self.prot_length)
        elif (self.effect == "missense" or self.effect == "nonsense" or
              self.effect == "coding_unknown"):
            eff_d = str(self.prot_pos) + "/" + str(self.prot_length)
            eff_d += "(" + self.aa_change + ")"
        elif self.effect == "promoter":
            eff_d = str(self.dist_from_5utr)
        elif self.effect == "CDS" or self.effect == "all":
            eff_d = str(self.prot_length)
        elif self.effect == "no-mutation":
            eff_d = "no-mutation"
        return(eff_d)
