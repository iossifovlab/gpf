from __future__ import unicode_literals
import pytest
import pandas as pd
from six import StringIO

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
def score_files_by_chunks():
    score = [
        pd.DataFrame({'SCORE': [1, 2, 3]}),
        pd.DataFrame({'SCORE': [4, 4, 5]}),
        pd.DataFrame({'SCORE': [6]})
    ]
    rankscore = [
        pd.DataFrame({'RANKSCORE': [1, 10, 100]}),
        pd.DataFrame({'RANKSCORE': [100, 1000, 10000]}),
        pd.DataFrame({'RANKSCORE': [1000000]})
    ]
    rankscore_zero_start = [
        pd.DataFrame({'RANKSCORE_0': [0, 1, 10]}),
        pd.DataFrame({'RANKSCORE_0': [100, 100, 1000]}),
        pd.DataFrame({'RANKSCORE_0': [10000]})
    ]
    return [score, score, rankscore, rankscore_zero_start,
            rankscore_zero_start]


@pytest.fixture
def score_files_with_start_end():
    score = [
        pd.DataFrame({'SCORE': [1, 2, 3], 'start': [5, 10, 20],
                      'end': [5, 11, 23]}),
        pd.DataFrame({'SCORE': [4, 4, 5], 'start': [5, 10, 20],
                      'end': [5, 11, 23]}),
        pd.DataFrame({'SCORE': [6], 'start': [100], 'end': [100]})
    ]
    rankscore = [
        pd.DataFrame({'RANKSCORE': [1, 10, 100], 'start': [5, 10, 20],
                      'end': [5, 10, 20]}),
        pd.DataFrame({'RANKSCORE': [100, 1000, 10000], 'start': [5, 10, 20],
                      'end': [5, 10, 20]}),
        pd.DataFrame({'RANKSCORE': [1000000], 'start': [100],
                      'end': [100]})
    ]
    rankscore_zero_start = [
        pd.DataFrame({'RANKSCORE_0': [0, 1, 10], 'start': [5, 10, 20],
                      'end': [5, 10, 20]}),
        pd.DataFrame({'RANKSCORE_0': [100, 100, 1000], 'start': [5, 10, 20],
                      'end': [5, 10, 20]}),
        pd.DataFrame({'RANKSCORE_0': [10000], 'start': [100],
                      'end': [100]})
    ]
    return [score, score, rankscore, rankscore_zero_start,
            rankscore_zero_start]


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
    return [6, 4, 7]


@pytest.fixture
def ranges():
    return {'RANKSCORE': [10.0, 10000.0], 'RANKSCORE_0': [0.0, 100000.0]}


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


@pytest.fixture
def expected_output_with_start_end(scores):
    score = "{},scores\n1.0,1.0\n2.0,2.0\n4.0,3.0\n3.0,4.0\n"\
            "5.0,5.0\n,6.0\n".format(scores[0])
    rankscore = "{},scores\n1.0,10.0\n2.0,100.0\n"\
                "2.0,1000.0\n,10000.0\n".format(scores[1])
    rankscore_zero_start =\
        "{},scores\n1.0,0.0\n1.0,1.0\n1.0,10.0\n2.0,100.0\n"\
        "1.0,1000.0\n1.0,10000.0\n,100000.0\n".format(scores[2])
    return [score, rankscore, rankscore_zero_start]


output = [MyStringIO(), MyStringIO(), MyStringIO()]
output_by_chunks = [MyStringIO(), MyStringIO(), MyStringIO()]
output_with_start_end = [MyStringIO(), MyStringIO(), MyStringIO()]


@pytest.fixture
def generate_histograms(mocker, score_files, scores, xscales, yscales,
                        bin_nums, ranges):
    mocker.patch('pandas.read_csv',
                 side_effect=lambda _, usecols, sep, header:
                 score_files.pop(0))
    mocker.patch('matplotlib.pyplot.savefig', side_effect=None)
    return GenerateScoresHistograms(['1'], output, scores, xscales, yscales,
                                    bin_nums, ranges)


@pytest.fixture
def generate_histograms_by_chunks(mocker, score_files_by_chunks, scores,
                                  xscales, yscales, bin_nums, ranges):
    mocker.patch('pandas.read_csv',
                 side_effect=lambda _, usecols, sep, header, chunksize,
                 low_memory: score_files_by_chunks.pop(0))
    mocker.patch('matplotlib.pyplot.savefig', side_effect=None)
    return GenerateScoresHistograms(['1'], output_by_chunks, scores, xscales,
                                    yscales, bin_nums, ranges, chunk_size=3)


@pytest.fixture
def generate_histograms_with_start_end(
        mocker, score_files_with_start_end, scores, xscales, yscales, bin_nums,
        ranges):
    mocker.patch('pandas.read_csv',
                 side_effect=lambda _, usecols, sep, header, chunksize,
                 low_memory: score_files_with_start_end.pop(0))
    mocker.patch('matplotlib.pyplot.savefig', side_effect=None)
    return GenerateScoresHistograms(
        ['1'], output_with_start_end, scores, xscales, yscales, bin_nums,
        ranges, chunk_size=3)


def test_generate_histogram(mocker, generate_histograms, expected_output):
    generate_histograms.generate_scores_histograms()
    print(output)

    assert output[0].getvalue() == expected_output[0]
    assert output[1].getvalue() == expected_output[1]
    assert output[2].getvalue() == expected_output[2]


def test_generate_histogram_by_chunks(
        mocker, generate_histograms_by_chunks, expected_output):
    generate_histograms_by_chunks.generate_scores_histograms()

    assert output_by_chunks[0].getvalue() == expected_output[0]
    assert output_by_chunks[1].getvalue() == expected_output[1]
    assert output_by_chunks[2].getvalue() == expected_output[2]


def test_generate_histogram_with_start_end(
        mocker, generate_histograms_with_start_end,
        expected_output_with_start_end):
    generate_histograms_with_start_end.generate_scores_histograms(
        start='start', end='end')

    print(output_with_start_end)

    assert output_with_start_end[0].getvalue() ==\
        expected_output_with_start_end[0]
    assert output_with_start_end[1].getvalue() ==\
        expected_output_with_start_end[1]
    assert output_with_start_end[2].getvalue() ==\
        expected_output_with_start_end[2]
