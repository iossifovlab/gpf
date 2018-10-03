'''
Created on Jan 16, 2018

@author: lubo
'''
from __future__ import print_function
from common_reports_api.permissions import get_datasets_by_study
from tests.pytest_marks import slow

@slow
def test_denovo_db():
    datasets_list = get_datasets_by_study("TESTdenovo_db")
    print(datasets_list)
    assert len(datasets_list) == 1
    datasets = datasets_list[0]

    assert len(datasets) == 1
    assert "TESTdenovo_db" in datasets


def test_iosiffov_2014():
    datasets_list = get_datasets_by_study("IossifovWE2014")
    print(datasets_list)
    assert len(datasets_list) == 1
    datasets = datasets_list[0]

    assert len(datasets) == 3
    assert "SSC" in datasets
    assert "SD_TEST" in datasets
    assert "SD" in datasets


def test_iosiffov_2012():
    datasets_list = get_datasets_by_study("IossifovWE2012")
    print(datasets_list)
    assert len(datasets_list) == 1
    datasets = datasets_list[0]

    assert len(datasets) == 0
