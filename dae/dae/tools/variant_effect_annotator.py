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
    T = [
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

    G = ["LGDs", "LoF", "nonsynonymous", "coding", "introns", "UTRs", "CNVs"]

    if types:
        if not groups:
            return T
        A = list(G)
        A.extend(T)
        return A
    if groups:
        return G
    return []


def get_effect_types_set(s):
    s = s.split(",")
    global LOF
    global nonsyn

    Groups = {
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
    R = []

    for i in s:
        try:
            R.extend(Groups[i])
        except KeyError:
            R.append(i)

    return set(R)
