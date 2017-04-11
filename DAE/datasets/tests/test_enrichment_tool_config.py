'''
Created on Feb 27, 2017

@author: lubo
'''


def test_enrichment_children_stats_vip(vip):
    res = vip.enrichment_children_stats
    print(res)


def test_enrichment_children_stats_sd(sd):
    children_stats = sd.enrichment_children_stats
    print(children_stats)

    assert children_stats['intellectual disability']['F'] == 85
    assert children_stats['intellectual disability']['M'] == 66

    assert children_stats['autism']['M'] == 3367  # 3367
    assert children_stats['autism']['F'] == 596

    assert children_stats['congenital heart disease']['F'] == 467  # 467
    assert children_stats['congenital heart disease']['M'] == 762  # 762

    assert children_stats['epilepsy']['F'] == 106
    assert children_stats['epilepsy']['M'] == 158

    assert children_stats['schizophrenia']['F'] == 248
    assert children_stats['schizophrenia']['M'] == 716

    assert children_stats['unaffected']['F'] == 1192  # 1192
    assert children_stats['unaffected']['M'] == 1111  # 1111
