'''
Created on Mar 1, 2018

@author: lubo
'''
from __future__ import print_function
from common_reports_api.variants import FamiliesReport


def test_families_report_iossifov_2014():
    fr = FamiliesReport('IossifovWE2014')
    assert fr is not None

    fr.build()
    print(fr)

    assert fr.families_total == 2516

    assert fr.children_counters is not None
    assert len(fr.children_counters) == 2

    cc = fr.children_counters[0]

    assert cc.phenotype_id == "autism"
    assert cc.children_female == 341
    assert cc.children_male == 2166
    assert cc.children_unspecified == 0
    assert cc.children_total == 2507

    cc = fr.children_counters[1]

    assert cc.phenotype_id == "unaffected"
    assert cc.children_female == 1011
    assert cc.children_male == 899
    assert cc.children_unspecified == 0
    assert cc.children_total == 1910
