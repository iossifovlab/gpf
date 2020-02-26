'''
Created on Oct 16, 2017

@author: lubo
'''
from dae.pheno.common import default_config, MeasureType
from dae.pheno.prepare.measure_classifier import MeasureClassifier


def test_fake_phenotype_data_ordinal_m4(fake_phenotype_data):
    measure_id = 'i1.m4'
    df = fake_phenotype_data.get_measure_values_df(measure_id)
    rank = len(df[measure_id].unique())
    assert rank == 9
    assert len(df) == 195

    measure_conf = default_config()
    classifier = MeasureClassifier(measure_conf)
    report = classifier.meta_measures(df[measure_id])
    assert classifier.classify(report) == MeasureType.ordinal
