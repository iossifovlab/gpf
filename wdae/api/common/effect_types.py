'''
Created on Jul 28, 2015

@author: lubo
'''
import operator

EFFECT_TYPES = {
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
        "Nonsense",
        "Frame-shift",
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


def build_effect_type_filter(data):
    if "effectTypes" not in data:
        return
    effects_string = data['effectTypes']
    effects = effects_string.split(',')
    result_effects = \
        reduce(operator.add,
               [EFFECT_TYPES[et] if et in EFFECT_TYPES else [et]
                for et in effects])
    data["effectTypes"] = ','.join(result_effects)
