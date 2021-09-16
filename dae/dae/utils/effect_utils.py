import itertools


class EffectTypesMixin(object):
    EFFECT_TYPES = [
        "3'UTR",
        "3'UTR-intron",
        "5'UTR",
        "5'UTR-intron",
        "frame-shift",
        "intergenic",
        "intron",
        "missense",
        "no-frame-shift",
        "no-frame-shift-newStop",
        "noEnd",
        "noStart",
        "non-coding",
        "non-coding-intron",
        "nonsense",
        "splice-site",
        "synonymous",
        "CDS",
        "CNV+",
        "CNV-",
    ]

    EFFECT_TYPES_MAPPING = {
        "Nonsense": ["nonsense"],
        "Frame-shift": ["frame-shift"],
        "Splice-site": ["splice-site"],
        "Missense": ["missense"],
        "No-frame-shift": ["no-frame-shift"],
        "No-frame-shift-newStop": ["no-frame-shift-newStop"],
        "noStart": ["noStart"],
        "noEnd": ["noEnd"],
        "Synonymous": ["synonymous"],
        "Non coding": ["non-coding"],
        "Intron": ["intron", "non-coding-intron"],
        "Intergenic": ["intergenic"],
        "3'-UTR": ["3'UTR", "3'UTR-intron"],
        "5'-UTR": ["5'UTR", "5'UTR-intron"],
        "CNV": ["CNV+", "CNV-"],
        "CNV+": ["CNV+"],
        "CNV-": ["CNV-"],
    }

    EFFECT_TYPES_UI_NAMING = {
        "nonsense": "Nonsense",
        "frame-shift": "Frame-shift",
        "splice-site": "Splice-site",
        "missense": "Missense",
        "no-frame-shift": "No-frame-shift",
        "no-frame-shift-newStop": "No-frame-shift-newStop",
        "synonymous": "Synonymous",
        "non-coding": "Non coding",
        "intron": "Intron",
        "non-coding-intron": "Intron",
    }
    EFFECT_GROUPS = {
        "coding": [
            "Nonsense",
            "Frame-shift",
            "Splice-site",
            "No-frame-shift-newStop",
            "Missense",
            "No-frame-shift",
            "noStart",
            "noEnd",
            "Synonymous",
        ],
        "noncoding": [
            "Non coding",
            "Intron",
            "Intergenic",
            "3'-UTR",
            "5'-UTR",
        ],
        "cnv": ["CNV+", "CNV-"],
        "lgds": [
            "Frame-shift",
            "Nonsense",
            "Splice-site",
            "No-frame-shift-newStop",
        ],
        "nonsynonymous": [
            "Nonsense",
            "Frame-shift",
            "Splice-site",
            "No-frame-shift-newStop",
            "Missense",
            "No-frame-shift",
            "noStart",
            "noEnd",
        ],
        "utrs": [
            "3'-UTR",
            "5'-UTR",
        ],
    }

    def _build_effect_types_groups(self, effect_types):
        etl = [
            self.EFFECT_GROUPS[et.lower()]
            if et.lower() in self.EFFECT_GROUPS
            else [et]
            for et in effect_types
        ]
        return list(itertools.chain.from_iterable(etl))

    def _build_effect_types_list(self, effect_types):
        etl = [
            self.EFFECT_TYPES_MAPPING[et]
            if et in self.EFFECT_TYPES_MAPPING
            else [et]
            for et in effect_types
        ]
        return list(itertools.chain.from_iterable(etl))

    def build_effect_types(self, effect_types, safe=True):
        if isinstance(effect_types, str):
            effect_types = effect_types.split(",")
        etl = [et.strip() for et in effect_types]
        etl = self._build_effect_types_groups(etl)
        etl = self._build_effect_types_list(etl)
        if safe:
            assert all([et in self.EFFECT_TYPES for et in etl])
        else:
            etl = [et for et in etl if et in self.EFFECT_TYPES]
        return etl

    def build_effect_types_naming(self, effect_types, safe=True):
        if isinstance(effect_types, str):
            effect_types = effect_types.split(",")
        assert isinstance(effect_types, list)
        if safe:
            assert all(
                [
                    et in self.EFFECT_TYPES
                    or et in list(self.EFFECT_TYPES_MAPPING.keys())
                    for et in effect_types
                ]
            )
        return [self.EFFECT_TYPES_UI_NAMING.get(et, et) for et in effect_types]

    def get_effect_types(self, safe=True, **kwargs):
        effect_types = kwargs.get("effectTypes", None)
        if effect_types is None:
            return None

        return self.build_effect_types(effect_types, safe)


def expand_effect_types(effect_types):
    if isinstance(effect_types, str):
        effect_types = [effect_types]

    effects = []
    for effect in effect_types:
        effect_lower = effect.lower()
        if effect_lower in EffectTypesMixin.EFFECT_GROUPS:
            effects += EffectTypesMixin.EFFECT_GROUPS[effect_lower]
        else:
            effects.append(effect)

    result = []
    for effect in effects:
        if effect not in EffectTypesMixin.EFFECT_TYPES_MAPPING:
            result.append(effect)
        else:
            result += EffectTypesMixin.EFFECT_TYPES_MAPPING[effect]
    return result


def ge2str(eff):
    return "|".join(["{}:{}".format(g.symbol, g.effect) for g in eff.genes])


def gd2str(eff):
    return "|".join(
        [
            "{}:{}".format(t.transcript_id, t.details)
            for t in eff.transcripts.values()
        ]
    )


def gene_effect_get_worst_effect(gs):
    if gs is None:
        return ""
    return ",".join([gs.worst])


def gene_effect_get_genes(gs):
    if gs is None:
        return ""
    genes_set = set([x.symbol for x in gs.genes])
    genes = sorted(list(genes_set))

    return ";".join(genes)
