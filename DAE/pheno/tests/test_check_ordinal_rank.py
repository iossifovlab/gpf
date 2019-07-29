'''
Created on Oct 16, 2017

@author: lubo
'''
from __future__ import unicode_literals
from pheno.common import default_config, MeasureType
from pheno.prepare.measure_classifier import MeasureClassifier


def test_fphdb_ordinal_m4(fphdb):
    measure_id = 'i1.m4'
    df = fphdb.get_measure_values_df(measure_id)
    rank = len(df[measure_id].unique())
    assert rank == 9
    assert len(df) == 195

    measure_conf = default_config()
    classifier = MeasureClassifier(measure_conf)
    report = classifier.meta_measures(df[measure_id])
    assert classifier.classify(report) == MeasureType.ordinal
