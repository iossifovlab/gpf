'''
Created on Nov 7, 2016

@author: lubo
'''
from __future__ import unicode_literals
import numpy as np
import pandas as pd

from enrichment_tool.background import SamochaBackground


def test_samocha_background_default():
    background = SamochaBackground()
    background.precompute()

    assert background.background is not None


def compare_samocha_backgrounds(df1, df2):
    assert np.all(df1['gene'] == df2['gene'])
    assert np.all(df1['M'] == df2['M'])

    assert np.all(df1['F'] == df2['F'])
    index = np.abs(df1['P_LGDS'] - df2['P_LGDS']) > 1E-8
    assert not np.any(index)

    index = np.abs(df1['P_LGDS'] - df2['P_LGDS']) < 1E-8
    assert np.all(index)

    index = np.abs(df1['P_MISSENSE'] - df2['P_MISSENSE']) < 1E-8
    assert np.all(index)

    index = np.abs(df1['P_SYNONYMOUS'] - df2['P_SYNONYMOUS']) < 1E-8
    assert np.all(index)


def test_compare_two_background_tables(samocha_background):
    df1 = samocha_background.background
    assert df1 is not None

    df2 = pd.read_csv(samocha_background.filename)
    assert df2 is not None

    compare_samocha_backgrounds(df1, df2)


def test_model_serialize(samocha_background):
    data = samocha_background.serialize()
    assert data is not None

    background2 = SamochaBackground()
    background2.deserialize(data)
    compare_samocha_backgrounds(
        samocha_background.background, background2.background)
