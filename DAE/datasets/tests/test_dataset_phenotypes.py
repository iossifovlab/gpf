'''
Created on Feb 17, 2017

@author: lubo
'''


def test_phenotypes_ssc(ssc):
    phenotypes = ssc.get_phenotypes()
    print(phenotypes)
    assert ['autism', 'unaffected'] == phenotypes


def test_phenotypes_sd(sd):
    phenotypes = sd.get_phenotypes()
    print(phenotypes)
    assert [
        'autism',
        'congenital heart disease',
        'epilepsy',
        'intellectual disability',
        'schizophrenia',
        'unaffected'
    ] == phenotypes


def test_phenotypes_vip(vip):
    phenotypes = vip.get_phenotypes()
    print(phenotypes)
    assert ['autism', 'unaffected'] == phenotypes


def test_children_stats_sd(sd):
    children_stats = sd.children_stats
    print(children_stats)

    assert children_stats['intellectual disability']['F'] == 85
    assert children_stats['intellectual disability']['M'] == 66

    # assert children_stats['autism']['M'] == 3367
    # assert children_stats['autism']['F'] == 596

    # assert children_stats['congenital heart disease']['F'] == 467
    # assert children_stats['congenital heart disease']['M'] == 762

    assert children_stats['epilepsy']['F'] == 106
    assert children_stats['epilepsy']['M'] == 158

    assert children_stats['schizophrenia']['F'] == 248
    assert children_stats['schizophrenia']['M'] == 716

    # assert children_stats['unaffected']['F'] == 1192
    # assert children_stats['unaffected']['M'] == 1111
