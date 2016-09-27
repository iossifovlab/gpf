'''
Created on Sep 27, 2016

@author: lubo
'''
import itertools

from query_variants import dae_query_variants


def test_dae_query():
    query = {
        'denovoStudies': 'ALL SSC',
        'geneRegion': 'chr5:140,117,933-140,900,259',
        'effectTypes': 'nonsense,frame-shift,splice-site',
    }

    vs = dae_query_variants(query)

    for v in itertools.chain(*vs):
        print(v)
        print("geneEffect: {}".format(
            getattr(v, 'geneEffect')))
        print("requestedGeneEffect: {}".format(
            getattr(v, 'requestedGeneEffects')))

        # assert getattr(v, 'geneEffect') == getattr(v, 'requestedGeneEffects')
        print("effectType: {}".format(
            v.atts['effectType']))


# def test_all_ssc_effect_type_vs_worst_effect_type():
#     query = {
#         'denovoStudies': 'ALL SSC',
#         # 'effectTypes': 'nonsense,frame-shift,splice-site',
#         'effectTypes': "Missense,Non-frame-shift,Synonymous,noEnd,noStart",
#     }
#
#     vs = dae_query_variants(query)
#     count = 0
#     for v in itertools.chain(*vs):
#         effect_type = v.atts['effectType']
#         worst_effect = v.requestedGeneEffects[0]['eff']
#         count += 1
#         print(v.atts)
#         assert effect_type == worst_effect
#
#     assert count > 0
#     print(count)


def test_effect_type_vs_worst_effect_counterexample():
    query = {
        "effectTypes": "Missense",
        "families": "All",
        "gender": "female,male",
        "geneRegion": "1:244552291-244552292",
        "presentInChild": "autism and unaffected,autism only,"
        "neither,unaffected only",
        "presentInParent": "neither",
        "variantTypes": "CNV,del,ins,sub",
        "genes": "All",
        "denovoStudies": "ALL SSC"
    }
    vs = dae_query_variants(query)
    count = 0
    for v in itertools.chain(*vs):
        effect_type = v.atts['effectType']
        worst_effect = v.requestedGeneEffects[0]['eff']
        count += 1
        print(v.atts)
        assert 'nonsense' == effect_type
        assert 'missense' == worst_effect

    assert count == 1
    print(count)
