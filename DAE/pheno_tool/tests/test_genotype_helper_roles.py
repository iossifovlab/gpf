'''
Created on Nov 17, 2016

@author: lubo
'''
from pheno_tool.tool import PhenoTool


def to_set(s):
    return set(s.split(','))


def test_prb_role_present_in_child(phdb, all_ssc_studies):
    h = PhenoTool(phdb, all_ssc_studies, roles=['prb'])

    assert set(['autism and unaffected', 'autism only']) == \
        to_set(h._present_in_child)


def test_sib_role_present_in_child(phdb, all_ssc_studies):
    h = PhenoTool(phdb, all_ssc_studies, roles=['sib'])

    assert set(['autism and unaffected', 'unaffected only']) == \
        to_set(h._present_in_child)


def test_prb_and_sib_role_present_in_child(phdb, all_ssc_studies):
    h = PhenoTool(phdb, all_ssc_studies, roles=['prb', 'sib'])

    assert set(['autism and unaffected',
                'autism only',
                'unaffected only']) == \
        to_set(h._present_in_child)


def test_mom_role_present_in_child(phdb, all_ssc_studies):
    h = PhenoTool(phdb, all_ssc_studies, roles=['mom'])

    assert 'neither' == h._present_in_child


def test_mom_and_prb_role_present_in_child(phdb, all_ssc_studies):
    h = PhenoTool(phdb, all_ssc_studies, roles=['prb', 'mom'])

    assert set(['autism and unaffected', 'autism only', 'neither']) == \
        to_set(h._present_in_child)


def test_mom_role_present_in_parent(phdb, all_ssc_studies):
    h = PhenoTool(phdb, all_ssc_studies, roles=['mom'])
    assert set(['mother only', 'mother and father']) == \
        to_set(h._present_in_parent)


def test_dad_role_present_in_parent(phdb, all_ssc_studies):
    h = PhenoTool(phdb, all_ssc_studies, roles=['dad'])
    assert set(['father only', 'mother and father']) == \
        to_set(h._present_in_parent)


def test_mom_and_dad_and_prb_role_present_in_parent(phdb, all_ssc_studies):
    h = PhenoTool(phdb, all_ssc_studies, roles=['dad', 'mom', 'prb'])
    assert set(['father only',
                'mother only',
                'mother and father',
                'neither']) == \
        to_set(h._present_in_parent)
