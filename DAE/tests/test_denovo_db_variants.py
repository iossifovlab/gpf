'''
Created on Apr 17, 2018

@author: lubo
'''
from __future__ import print_function
import os
import pytest
import VariantAnnotation


@pytest.fixture(scope='session')
def denovo_db_full():
    from DAE import vDB

    assert 'TESTdenovo_db' in vDB._studies
    dst = vDB._studies['TESTdenovo_db']
    filename = dst.vdb._config.get(dst._configSection, 'denovoCalls.files')
    dirname = os.path.dirname(filename)

    filename = os.path.join(
        dirname,
        "denovo-db.variants-annotated.tsv")
    print("denovo db full:", filename)

    dst.vdb._config.set(dst._configSection, "denovoCalls.full.files", filename)
    dst = vDB.get_study("TESTdenovo_db")

    return dst


def test_denovo_db_reconfigure(denovo_db_full):

    vs = denovo_db_full.get_denovo_variants(
        regionS="X:1-155270560", callSet='full')
    vs = list(vs)
    assert vs

    print("variants found:", len(vs))
    assert len(vs) == 5060


def test_denovo_db_autism_on_X(denovo_db_full):

    vs = denovo_db_full.get_denovo_variants(
        regionS="X:1-155270560", callSet='full')
    vs = list(vs)
    assert vs

    res = []
    for v in vs:
        if v.atts['phenotype'] == 'autism':
            res.append(v)
    print("autism variants found:", len(res))
    assert len(res) == 4589


def test_denovo_db_autism_coding_in_prb_on_X(denovo_db_full):
    coding_effects = VariantAnnotation.get_effect_types_set("coding")
    vs = denovo_db_full.get_denovo_variants(
        inChild="prb",
        effectTypes=coding_effects,
        regionS="X:1-155270560",
        callSet='full'
    )
    vs = list(vs)
    assert vs
    res = []
    for v in vs:
        if v.atts['phenotype'] == 'autism':
            res.append(v)
    print("coding autism variants found:", len(res))
    assert len(res) == 144


def test_denovo_db_autism_coding_in_prb_on_X_problematic(denovo_db_full):
    coding_effects = VariantAnnotation.get_effect_types_set("coding")
    vs = denovo_db_full.get_denovo_variants(
        inChild="prb",
        effectTypes=coding_effects,
        regionS="X:1-155270560",
        callSet='full'
    )
    vs = list(vs)
    assert vs
    res = []
    for v in vs:
        if v.atts['phenotype'] == 'autism':
            res.append(v)
    print("coding autism variants found:", len(res))
    assert len(res) == 144

    count = 0
    for v in res:
        prb_ids = set()
        for p, a_count in zip(v.memberInOrder, v.bestSt[1, :]):
            if p.role != "prb" or a_count == 0:
                continue
            prb_ids.add(p.personId)
        if len(prb_ids) == 0:
            print("incompatible role/best state:",
                  v.atts['studyName'],  v.location, v.variant,
                  v.inChS, v.memberInOrder)
            print(v.bestSt)
            count += 1
    print("problematic variants:", count)
    assert count == 0


def test_denovo_db_problematic_variant(denovo_db_full):
    vs = denovo_db_full.get_denovo_variants(
        regionS="X:153588164-153588164",
        callSet='full'
    )
    vs = list(vs)
    assert len(vs) == 1
    v = vs[0]
    print("testing role/best state:",
          v.atts['studyName'],  v.location, v.variant,
          v.inChS, v.memberInOrder)
    print(v.bestSt)

    assert 'sib' in v.inChS
    assert 'prb' not in v.inChS
