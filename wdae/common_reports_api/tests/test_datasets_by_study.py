'''
Created on Jan 16, 2018

@author: lubo
'''
from common_reports_api.permissions import get_datasets_by_study


def test_denovo_db():
    datasets_list = get_datasets_by_study("denovo_db")
    print(datasets_list)
    assert len(datasets_list) == 1
    datasets = datasets_list[0]

    assert len(datasets) == 1
    assert "denovo_db" in datasets


def test_iosiffov_2014():
    datasets_list = get_datasets_by_study("IossifovWE2014")
    print(datasets_list)
    assert len(datasets_list) == 1
    datasets = datasets_list[0]

    assert len(datasets) == 2
    assert "SSC" in datasets
    assert "SD" in datasets


def test_iosiffov_2012():
    datasets_list = get_datasets_by_study("IossifovWE2012")
    print(datasets_list)
    assert len(datasets_list) == 1
    datasets = datasets_list[0]

    assert len(datasets) == 0
