'''
Created on Nov 8, 2016

@author: lubo
'''
from collections import Counter
from enrichment_tool.config import ChildrenStats


def test_count_unaffected(denovo_studies):
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

    stats = ChildrenStats.count(studies, 'sib')
    print(stats)

    res = ChildrenStats.build(denovo_studies)
    print(res)
    assert res['unaffected'] == counter
