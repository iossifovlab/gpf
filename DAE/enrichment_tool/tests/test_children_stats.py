'''
Created on Nov 8, 2016

@author: lubo
'''
from collections import Counter
from enrichment_tool.genotype_helper import GenotypeHelper as GH


def test_count_unaffected(denovo_studies):
    seen = set()
    counter = Counter()
    studies = denovo_studies
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


def test_children_stats_simple(autism_studies, unaffected_studies):

    gh = GH.from_studies(autism_studies, 'prb')
    children_stats = gh.get_children_stats()

    assert 596 == children_stats['F']
    assert 3367 == children_stats['M']

    gh = GH.from_studies(unaffected_studies, 'sib')
    children_stats = gh.get_children_stats()

    assert 1111 == children_stats['M']
    assert 1192 == children_stats['F']


def test_children_stats_dataset(sd):
    gh = GH.from_dataset(sd, 'phenotype', 'autism')
    children_stats = gh.get_children_stats()

    assert 596 == children_stats['F']
    assert 3367 == children_stats['M']

    # gh = GH.from_studies(unaffected_studies, 'sib')
    gh = GH.from_dataset(sd, 'phenotype', 'unaffected')
    children_stats = gh.get_children_stats()

    assert 1111 == children_stats['M']
    assert 1192 == children_stats['F']
