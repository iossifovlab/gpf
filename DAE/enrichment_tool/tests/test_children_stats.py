'''
Created on Nov 8, 2016

@author: lubo
'''
from collections import Counter


def test_count_unaffected(denovo_studies, children_stats):
    seen = set()
    counter = Counter()
    studies = denovo_studies.get_studies('unaffected')
    print([st.name for st in studies])
    for st in studies:
        for fid, fam in st.families.items():
            for p in fam.memberInOrder[2:]:
                iid = "{}:{}".format(fid, p.personId)
                if iid in seen:
                    continue
                if p.role != 'sib':
                    continue

                counter[p.gender] += 1
                seen.add(iid)
    print(counter)

    assert counter['M'] > 0
    assert counter['F'] > 0
    assert 2303 == counter['F'] + counter['M']

    assert children_stats['unaffected'] == counter


def test_children_stats_simple(children_stats):

    assert 596 == children_stats['autism']['F']
    assert 3367 == children_stats['autism']['M']

    assert 1111 == children_stats['unaffected']['M']
    assert 1192 == children_stats['unaffected']['F']
