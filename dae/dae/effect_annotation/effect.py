class Effect(object):

    def __init__(self, effect_name):
        self.effect = effect_name
        self.gene = None
        self.transcript_id = None
        self.strand = None
        self.prot_pos = None
        self.non_coding_pos = None
        self.prot_length = None
        self.length = None
        self.which_intron = None
        self.how_many_introns = None
        self.dist_from_coding = None
        self.aa_change = None
        self.dist_from_acceptor = None
        self.dist_from_donor = None
        self.intron_length = None
        self.mRNA_length = None
        self.mRNA_position = None
        self.ref_aa = None
        self.alt_aa = None
        self.dist_from_5utr = None

    def __repr__(self):
        return (
            "Effect gene:{} trID:{} strand:{} effect:{} "
            "protein pos:{}/{} aa: {}".format(
                self.gene,
                self.transcript_id,
                self.strand,
                self.effect,
                self.prot_pos,
                self.prot_length,
                self.aa_change,
            )
        )

    def create_effect_details(self):
        eff_data = [
            (["noStart", "noEnd", "CDS", "all"], str(self.prot_length)),
            (
                [
                    "intron",
                    "5'UTR-intron",
                    "3'UTR-intron",
                    "non-coding-intron",
                ],
                str(self.which_intron) + "/" + str(self.how_many_introns),
            ),
            (
                [
                    "intron",
                    "5'UTR-intron",
                    "3'UTR-intron",
                    "non-coding-intron",
                ],
                "[" + str(self.dist_from_coding) + "]",
            ),
            (
                [
                    "no-frame-shift",
                    "no-frame-shift-newStop",
                    "frame-shift",
                    "splice-site",
                    "synonymous",
                    "missense",
                    "nonsense",
                    "coding_unknown",
                ],
                str(self.prot_pos) + "/" + str(self.prot_length),
            ),
            (
                [
                    "no-frame-shift",
                    "no-frame-shift-newStop",
                    "missense",
                    "nonsense",
                    "coding_unknown",
                ],
                "(" + str(self.aa_change) + ")",
            ),
            (["no-mutation"], "no-mutation"),
            (["5'UTR", "3'UTR"], str(self.dist_from_coding)),
            (["non-coding", "unknown", "tRNA:ANTICODON"], str(self.length)),
            (["promoter"], str(self.dist_from_5utr)),
        ]

        return "".join(
            [data for cond, data in eff_data if self.effect in cond]
        )


class EffectFactory(object):
    @classmethod
    def create_effect(cls, effect_name):
        return Effect(effect_name)

    @classmethod
    def create_effect_with_tm(cls, effect_name, transcript_model):
        ef = cls.create_effect(effect_name)
        ef.gene = transcript_model.gene
        ef.strand = transcript_model.strand
        try:
            ef.transcript_id = transcript_model.tr_name
        except AttributeError:
            ef.transcript_id = transcript_model.tr_id

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
        # ef.prot_pos, _ = request.get_protein_position()

        ref_aa, alt_aa = request.get_amino_acids()
        ef.aa_change = "{}->{}".format(",".join(ref_aa), ",".join(alt_aa))

        ef.ref_aa = ref_aa
        ef.alt_aa = alt_aa

        return ef

    @classmethod
    def create_intronic_non_coding_effect(
        cls, effect_type, request, start, end, index
    ):
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
            ef.which_intron = ef.how_many_introns - index + 1
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
