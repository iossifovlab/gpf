'''
Created on Sep 27, 2016

@author: lubo
'''
import itertools

from query_variants import dae_query_variants, generate_response


def test_dae_query():
    query = {
        'denovoStudies': 'ALL SSC',
        'geneRegion': 'chr5:140,117,933-140,900,259',
        'effectTypes': 'nonsense,frame-shift,splice-site',
    }

    vs = dae_query_variants(query)

    for v in itertools.chain(*vs):
        assert v


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
        assert 'nonsense' == effect_type
        assert 'missense' == worst_effect

    assert count == 1


def variant_response_dict(v, atts):
    g = generate_response([v], atts)
    names = g.next()
    vr = g.next()
    d = dict(zip(names, vr))
    return d


def test_effect_type_genes_list():
    query = {
        'denovoStudies': 'ALL SSC',
        'geneRegion': 'chr5:140,117,933-140,900,259',
    }
    columns = ['worstEffect', 'geneEffect', 'genes']
    vs = dae_query_variants(query)
    count = 0
    for v in itertools.chain(*vs):
        count += 1
        d = variant_response_dict(v, columns)

        assert 'worst requested effect' in d
        assert 'all effects' in d
        assert 'genes' in d

        assert d['worst requested effect'] == \
            v.requestedGeneEffects[0]['eff']

    assert 19 == count
