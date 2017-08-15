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

    def __init__(self, effect_name):
        self.effect = effect_name

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


class EffectFactory:
    @classmethod
    def create_effect(cls, effect_name):
        return Effect(effect_name)

    @classmethod
    def create_effect_with_tm(cls, effect_name, transcript_model):
        ef = cls.create_effect(effect_name)
        ef.gene = transcript_model.gene
        ef.strand = transcript_model.strand
        ef.transcript_id = transcript_model.trID
        return ef

    @classmethod
    def create_effect_with_request(cls, effect_name, request):
        ef = cls.create_effect_with_tm(effect_name, request.transcript_model)
        ef.mRNA_length = request.get_exonic_length()
        ef.mRNA_position = request.get_exonic_position()
        return ef

    @classmethod
    def create_effect_with_prot_length(cls, effect_name, request):
        ef = cls.create_effect_with_request(effect_name, request)
        ef.prot_length = request.get_protein_length()
        return ef

    @classmethod
    def create_effect_with_prot_pos(cls, effect_name, request):
        ef = cls.create_effect_with_prot_length(effect_name, request)
        start_prot, _ = request.get_protein_position()
        ef.prot_pos = start_prot
        return ef

    @classmethod
    def create_effect_with_aa_change(cls, effect_name, request):
        ef = cls.create_effect_with_prot_pos(effect_name, request)

        ref_aa, alt_aa = request.get_amino_acids()
        ef.aa_change = "{}->{}".format(
            ",".join(ref_aa),
            ",".join(alt_aa)
        )
        return ef

    @classmethod
    def create_intronic_non_coding_effect(cls, effect_type, request, start,
                                          end, index):
        ef = cls.create_effect_with_prot_length(effect_type, request)
        dist_left = request.variant.position - start - 1
        dist_right = end - request.variant.ref_position_last
        ef.dist_from_coding = min(dist_left, dist_right)

        ef.how_many_introns = len(request.transcript_model.exons) - 1
        ef.intron_length = end - start - 1
        if request.transcript_model.strand == "+":
            ef.dist_from_acceptor = dist_right
            ef.dist_from_donor = dist_left
            ef.which_intron = index
        else:
            ef.dist_from_acceptor = dist_left
            ef.dist_from_donor = dist_right
            ef.which_intron = ef.how_many_introns - \
                index + 1
        return ef

    @classmethod
    def create_intronic_effect(cls, effect_type, request, start, end, index):
        ef = cls.create_intronic_non_coding_effect(
            effect_type, request, start, end, index
        )
        if request.transcript_model.strand == "+":
            ef.prot_pos = request.get_protein_position_for_pos(end)
        else:
            ef.prot_pos = request.get_protein_position_for_pos(start)
        return ef
