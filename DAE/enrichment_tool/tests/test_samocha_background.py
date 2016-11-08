'''
Created on Nov 7, 2016

@author: lubo
'''
import numpy as np
import pandas as pd

from enrichment_tool.background import SamochaBackground
import pytest


@pytest.fixture(scope='module')
def background(request):
    bg = SamochaBackground()
    bg.precompute()
    return bg


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


def test_compare_two_background_tables(background):
    df1 = background.background
    assert df1 is not None

    df2 = pd.read_csv(background.filename)
    assert df2 is not None

    compare_samocha_backgrounds(df1, df2)


def test_model_serialize(background):
    data = background.serialize()
    assert data is not None

    background2 = SamochaBackground()
    background2.deserialize(data)
    compare_samocha_backgrounds(
        background.background, background2.background)
