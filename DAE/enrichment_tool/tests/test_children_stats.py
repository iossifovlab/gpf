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


def test_children_stats_intellectual_disability_sd(sd):
    gh = GH.from_dataset(sd, 'phenotype', 'intellectual disability')
    children_stats = gh.get_children_stats()

    assert children_stats['F'] == 85
    assert children_stats['M'] == 66


def test_children_stats_autism_sd(sd):
    gh = GH.from_dataset(sd, 'phenotype', 'autism')
    children_stats = gh.get_children_stats()

    assert children_stats['M'] == 3367  # 3367
    assert children_stats['F'] == 596


def test_children_stats_congenital_heart_disease_sd(sd):
    gh = GH.from_dataset(sd, 'phenotype', 'congenital heart disease')
    children_stats = gh.get_children_stats()

    assert children_stats['F'] == 467  # 467
    assert children_stats['M'] == 762  # 762


def test_children_stats_epilepsy_sd(sd):
    gh = GH.from_dataset(sd, 'phenotype', 'epilepsy')
    children_stats = gh.get_children_stats()

    assert children_stats['F'] == 106
    assert children_stats['M'] == 158


def test_children_stats_schizophrenia_sd(sd):
    gh = GH.from_dataset(sd, 'phenotype', 'schizophrenia')
    children_stats = gh.get_children_stats()

    assert children_stats['F'] == 248
    assert children_stats['M'] == 716


def test_children_stats_unaffected_sd(sd):
    gh = GH.from_dataset(sd, 'phenotype', 'unaffected')
    children_stats = gh.get_children_stats()

    assert children_stats['F'] == 1192  # 1192
    assert children_stats['M'] == 1111  # 1111
