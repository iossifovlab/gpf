from __future__ import unicode_literals
import pytest
import pandas as pd
from io import StringIO

from tools.generate_histogram import GenerateScoresHistograms


class MyStringIO(StringIO):

    def __add__(self, other):
        return ''


@pytest.fixture
def score_files():
    score = pd.DataFrame({'SCORE': [1, 2, 3, 4, 4, 5, 6]})
    rankscore = pd.DataFrame({'RANKSCORE': [1, 10, 100, 100, 1000, 10000]})
    rankscore_zero_start =\
        pd.DataFrame({'RANKSCORE_0': [0, 1, 10, 100, 100, 1000, 10000]})
    return [score, rankscore, rankscore_zero_start]


@pytest.fixture
def scores():
    return ['SCORE', 'RANKSCORE', 'RANKSCORE_0']


@pytest.fixture
def xscales():
    return ['linear', 'log', 'log']


@pytest.fixture
def yscales():
    return ['log', 'linear', 'log']


@pytest.fixture
def bin_nums():
    return [5, 4, 7]


@pytest.fixture
def ranges():
    return {'RANKSCORE': [10, 10000], 'RANKSCORE_0': [0, 100000]}


@pytest.fixture
def expected_output(scores):
    score = "{},scores\n1.0,1.0\n1.0,2.0\n1.0,3.0\n2.0,4.0\n"\
            "2.0,5.0\n,6.0\n".format(scores[0])
    rankscore = "{},scores\n1.0,10.0\n2.0,100.0\n"\
                "2.0,1000.0\n,10000.0\n".format(scores[1])
    rankscore_zero_start =\
        "{},scores\n1.0,0.0\n1.0,1.0\n1.0,10.0\n2.0,100.0\n"\
        "1.0,1000.0\n1.0,10000.0\n,100000.0\n".format(scores[2])
    return [score, rankscore, rankscore_zero_start]


output = [MyStringIO(), MyStringIO(), MyStringIO()]


@pytest.fixture
def generate_histograms(mocker, score_files, scores):

    mocker.patch('pandas.read_csv',
                 side_effect=lambda _, usecols, sep, **kwargs: score_files.pop(0))
    mocker.patch('matplotlib.pyplot.savefig', side_effect=None)
    return GenerateScoresHistograms(['1'], output, scores)


def test_generate_histogram(mocker, generate_histograms, scores, xscales,
                            yscales, bin_nums, ranges, expected_output):
    generate_histograms.generate_scores_histograms(xscales, yscales,
                                                   bin_nums, ranges)

    assert output[0].getvalue() == expected_output[0]
    assert output[1].getvalue() == expected_output[1]
    assert output[2].getvalue() == expected_output[2]
