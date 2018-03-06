'''
Created on Mar 5, 2018

@author: lubo
'''
from __future__ import print_function

import pandas as pd
import numpy as np

from variants.annotator import AlleleFrequencyAnnotator
import pytest
from variants.loader import RawVariantsLoader


def test_allele_freq_annotator_parquet_experiment(nvcf, temp_filename):

    annotator = AlleleFrequencyAnnotator(nvcf.ped_df, nvcf.vcf, nvcf.vars_df)
    assert annotator is not None

    vars_df = annotator.annotate()
    assert vars_df is not None

    vars_df.to_parquet(temp_filename)

    vars1_df = pd.read_parquet(temp_filename)

    for v1, v2 in zip(vars_df.to_dict(orient='record'),
                      vars1_df.to_dict(orient='record')):
        for k in v1.keys():
            res = v1[k] == v2[k]
            if isinstance(res, np.ndarray):
                assert all(list(v1[k] == v2[k]))
            else:
                assert v1[k] == v2[k]


def test_allele_freq_annotator_csv_experiment(nvcf, temp_filename):

    annotator = AlleleFrequencyAnnotator(nvcf.ped_df, nvcf.vcf, nvcf.vars_df)
    assert annotator is not None

    vars_df = annotator.annotate()
    assert vars_df is not None

    vars_df.to_csv(temp_filename, index=False)

    vars1_df = RawVariantsLoader.load_annotation_file(
        temp_filename, sep=",")

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
