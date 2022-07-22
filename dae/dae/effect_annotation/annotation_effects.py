#!/bin/env python

# October 25th 2013
# written by Ewa


LOF = ["splice-site", "frame-shift", "nonsense", "no-frame-shift-newStop"]
nonsyn = [
    "splice-site",
    "frame-shift",
    "nonsense",
    "no-frame-shift-newStop",
    "missense",
    "noStart",
    "noEnd",
    "no-frame-shift",
]


def get_effect_types(types=True, groups=False):
    """Produce collection of effect types."""
    effect_types = [
        "tRNA:ANTICODON",
        "splice-site",
        "frame-shift",
        "nonsense",
        "no-frame-shift-newStop",
        "noStart",
        "noEnd",
        "missense",
        "no-frame-shift",
        "CDS",
        "synonymous",
        "coding_unknown",
        "3'UTR",
        "5'UTR",
        "intron",
        "non-coding",
        "5'UTR-intron",
        "3'UTR-intron",
        "promoter",
        "non-coding-intron",
        "unknown",
        "intergenic",
        "no-mutation",
        "CNV-",
        "CNV+",
    ]

    effect_groups = [
        "LGDs", "LoF", "nonsynonymous", "coding", "introns", "UTRs", "CNVs"]

    if types:
        if not groups:
            return effect_types
        result = list(effect_groups)
        result.extend(effect_types)
        return result
    if groups:
        return effect_groups
    return []


def get_effect_types_set(effect_types):
    """Split comma separated list of effect types."""
    effect_types = effect_types.split(",")

    groups = {
        "LGDs": LOF,
        "LoF": LOF,
        "introns": [
            "intron",
            "non-coding-intron",
            "5'UTR-intron",
            "3'UTR-intron",
        ],
        "UTRs": ["3'UTR", "5'UTR", "5'UTR-intron", "3'UTR-intron"],
        "coding": [
            "splice-site",
            "frame-shift",
            "nonsense",
            "no-frame-shift-newStop",
            "noStart",
            "noEnd",
            "missense",
            "no-frame-shift",
            "CDS",
            "synonymous",
        ],
        "nonsynonymous": [
            "splice-site",
            "frame-shift",
            "nonsense",
            "no-frame-shift-newStop",
            "noStart",
            "noEnd",
            "missense",
            "no-frame-shift",
            "CDS",
        ],
        "CNVs": ["CNV+", "CNV-"],
    }
    result = []

    for effect_type in effect_types:
        if effect_type in groups:
            result.extend(groups[effect_type])
        else:
            result.append(effect_type)

    return set(result)
