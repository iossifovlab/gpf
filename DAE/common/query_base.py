'''
Created on Feb 6, 2017

@author: lubo
'''
import itertools


class EffectTypesBase(object):
    EFFECT_TYPES = [
        "3'UTR",
        "3'UTR-intron",
        "5'UTR",
        "5'UTR-intron",
        'frame-shift',
        'intergenic',
        'intron',
        'missense',
        'no-frame-shift',
        'no-frame-shift-newStop',
        'noEnd',
        'noStart',
        'non-coding',
        'non-coding-intron',
        'nonsense',
        'splice-site',
        'synonymous',
        'CDS',
        'CNV+',
        'CNV-',
    ]

    EFFECT_TYPES_MAPPING = {
        "Nonsense": ["nonsense"],
        "Frame-shift": ["frame-shift"],
        "Splice-site": ["splice-site"],
        "Missense": ["missense"],
        "Non-frame-shift": ["no-frame-shift"],
        "noStart": ["noStart"],
        "noEnd": ["noEnd"],
        "Synonymous": ["synonymous"],
        "Non coding": ["non-coding"],
        "Intron": ["intron"],
        "Intergenic": ["intergenic"],
        "3'-UTR": ["3'UTR", "3'UTR-intron"],
        "5'-UTR": ["5'UTR", "5'UTR-intron"],
        "CNV": ["CNV+", "CNV-"],
        "CNV+": ["CNV+"],
        "CNV-": ["CNV-"],
    }

    EFFECT_GROUPS = {
        "coding": [
            "Nonsense",
            "Frame-shift",
            "Splice-site",
            "Missense",
            "Non-frame-shift",
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
        "cnv": [
            "CNV+",
            "CNV-"
        ],
        "lgds": [
            "Frame-shift",
            "Nonsense",
            "Splice-site",
        ],
        "nonsynonymous": [
            "Nonsense",
            "Frame-shift",
            "Splice-site",
            "Missense",
            "Non-frame-shift",
            "noStart",
            "noEnd",
        ],
        "utrs": [
            "3'-UTR",
            "5'-UTR",
        ]
    }

    def _build_effect_types_groups(self, effect_types):
        etl = [
            self.EFFECT_GROUPS[
                et.lower()] if et.lower() in self.EFFECT_GROUPS else [et]
            for et in effect_types
        ]
        return list(itertools.chain.from_iterable(etl))

    def _build_effect_types_list(self, effect_types):
        etl = [
            self.EFFECT_TYPES_MAPPING[et]
            if et in self.EFFECT_TYPES_MAPPING else [et]
            for et in effect_types]
        return list(itertools.chain.from_iterable(etl))

    def _build_(self):
        pass

    def build_effect_types(self, effect_types, safe=True):
        etl = [et.strip() for et in effect_types.split(',')]
        etl = self._build_effect_types_groups(etl)
        etl = self._build_effect_types_list(etl)
        if safe:
            assert all([et in self.EFFECT_TYPES for et in etl])
        else:
            etl = [et for et in etl if et in self.EFFECT_TYPES]
        return etl

    def get_effect_types(self, safe=True, **kwargs):
        assert 'effectTypes' in kwargs

        effect_types = kwargs['effectTypes']

        return self.build_effect_types(effect_types, safe)


class VariantTypesBase(object):
    VARIANT_TYPES = [
        'del', 'ins', 'sub', 'CNV'
    ]

    def get_variant_types(self, safe=True, **kwargs):
        if 'variantTypes' not in kwargs:
            return None
        variant_types = kwargs['variantTypes']
        if safe:
            assert all([vt in self.VARIANT_TYPES for vt in variant_types])
        variant_types = [
            vt for vt in variant_types if vt in self.VARIANT_TYPES
        ]
        if not variant_types:
            return None
        if set(variant_types) == set(self.VARIANT_TYPES):
            return None
        return variant_types


class QueryBase(EffectTypesBase, VariantTypesBase):

    PRESENT_IN_PARENT_TYPES = [
        "mother only", "father only",
        "mother and father", "neither",
    ]

    PRESENT_IN_CHILD_TYPES = [
        "autism only",
        "unaffected only",
        "autism and unaffected",
        "proband only",
        "sibling only",
        "proband and sibling",
        "neither",
    ]

    IN_CHILD_TYPES = [
        'prb',
        'sib',
        'prbM',
        'prbF',
        'sibM',
        'sibF',
    ]

    @staticmethod
    def idlist_get(named_list, name):
        for el in named_list:
            if name == el['id']:
                return el
        return None
