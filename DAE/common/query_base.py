'''
Created on Feb 6, 2017

@author: lubo
'''


class QueryBase(object):
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
        'CNV-', ]

    VARIANT_TYPES = [
        'del', 'ins', 'sub', 'CNV']

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
