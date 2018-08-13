'''
Created on Oct 17, 2017

@author: lubo
'''


def test_single_variant_region(ssc):
    data = {
        u'gender': [u'female', u'male'],
        u'regions': [u'5:175995815'],
        u'effectTypes': [u'Nonsense', u'Frame-shift', u'Splice-site'],
        u'presentInChild': [u'neither'],
        u'variantTypes': [u'sub', u'ins', u'del', u'CNV'],
        u'presentInParent': {
            u'rarity': {
                u'maxFreq': None,
                u'minFreq': None,
                u'ultraRare': True
            },
            u'presentInParent': [
                u'father only',
                u'mother only',
                u'mother and father'
            ]
        },
        u'datasetId': u'SSC'
    }
    vs = ssc.get_denovo_variants(**data)
    res = [v for v in vs]
    assert len(res) == 0

    vs = ssc.get_transmitted_variants(**data)
    res = [v for v in vs]
    assert len(res) == 1
