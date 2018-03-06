'''
Created on Mar 5, 2018

@author: lubo
'''
from __future__ import print_function

import pytest

import numpy as np
from variants.annotate_allele_frequencies import VcfAlleleFrequencyAnnotator
from variants.loader import RawVariantsLoader


def test_allele_freq_annotator_parquet_experiment(nvcf, temp_filename):

    annotator = VcfAlleleFrequencyAnnotator(nvcf)
    assert annotator is not None

    vars_df = annotator.annotate(nvcf.vars_df, nvcf.vcf_vars)
    assert vars_df is not None

    RawVariantsLoader.save_annotation_file(
        vars_df, temp_filename, storage='parquet')
    vars1_df = RawVariantsLoader.load_annotation_file(
        temp_filename, storage='parquet')

    for v1, v2 in zip(vars_df.to_dict(orient='record'),
                      vars1_df.to_dict(orient='record')):
        for k in v1.keys():
            res = v1[k] == v2[k]
            if isinstance(res, np.ndarray):
                assert all(list(v1[k] == v2[k]))
            else:
                assert v1[k] == v2[k]


def test_allele_freq_annotator_csv_experiment(nvcf, temp_filename):

    annotator = VcfAlleleFrequencyAnnotator(nvcf)
    assert annotator is not None

    vars_df = annotator.annotate(nvcf.vars_df, nvcf.vcf_vars)
    assert vars_df is not None

    RawVariantsLoader.save_annotation_file(
        vars_df, temp_filename, storage='csv')
    vars1_df = RawVariantsLoader.load_annotation_file(
        temp_filename, storage='csv')

    print(vars1_df.head())

    for v1, v2 in zip(vars_df.to_dict(orient='record'),
                      vars1_df.to_dict(orient='record')):
        for k in v1.keys():
            res = v1[k] == v2[k]
            if isinstance(res, np.ndarray):
                assert np.allclose(v1[k], v2[k], rtol=1e-5)
            elif isinstance(v1[k], float):
                assert v1[k] == pytest.approx(v2[k], 1e-6)
            else:
                assert v1[k] == v2[k]
