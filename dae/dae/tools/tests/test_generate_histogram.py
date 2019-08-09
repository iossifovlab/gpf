import pytest
import numpy as np
import pandas as pd
from six import StringIO

from dae.tools.generate_histogram import ScoreHistogramInfo,\
    GenerateScoresHistograms

# pytestmark = pytest.mark.xfail


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
def histogram_info_1(scores, xscales, yscales, bin_nums, ranges):
    return ScoreHistogramInfo(
        scores[0], scores[0], None, xscales[0], yscales[0], bin_nums[0],
        ranges.get(scores[0], None))


@pytest.fixture
def histogram_info_2(scores, xscales, yscales, bin_nums, ranges):
    return ScoreHistogramInfo(
        scores[1], scores[1], None, xscales[1], yscales[1], bin_nums[1],
        ranges.get(scores[1], None))


@pytest.fixture
def histogram_info_3(scores, xscales, yscales, bin_nums, ranges):
    return ScoreHistogramInfo(
        scores[2], scores[2], None, xscales[2], yscales[2], bin_nums[2],
        ranges.get(scores[2], None))


@pytest.fixture
def histogram_info(histogram_info_1, histogram_info_2, histogram_info_3):
    histogram_info_1.output_file = output[0]
    histogram_info_2.output_file = output[1]
    histogram_info_3.output_file = output[2]

    return [histogram_info_1, histogram_info_2, histogram_info_3]


@pytest.fixture
def histogram_info_by_chunks(
        histogram_info_1, histogram_info_2, histogram_info_3):
    histogram_info_1.output_file = output_by_chunks[0]
    histogram_info_2.output_file = output_by_chunks[1]
    histogram_info_3.output_file = output_by_chunks[2]

    return [histogram_info_1, histogram_info_2, histogram_info_3]


@pytest.fixture
def histogram_info_with_start_end(
        histogram_info_1, histogram_info_2, histogram_info_3):
    histogram_info_1.output_file = output_with_start_end[0]
    histogram_info_2.output_file = output_with_start_end[1]
    histogram_info_3.output_file = output_with_start_end[2]

    return [histogram_info_1, histogram_info_2, histogram_info_3]


@pytest.fixture
def generate_histograms(mocker, score_files, histogram_info):
    mocker.patch('pandas.read_csv',
                 side_effect=lambda _, usecols, sep, header:
                 score_files.pop(0))
    mocker.patch('matplotlib.pyplot.savefig', side_effect=None)

    return GenerateScoresHistograms(['1'], histogram_info)


@pytest.fixture
def generate_histograms_by_chunks(
        mocker, score_files_by_chunks, histogram_info_by_chunks):
    mocker.patch('pandas.read_csv',
                 side_effect=lambda _, usecols, sep, header, chunksize,
                 low_memory: score_files_by_chunks.pop(0))
    mocker.patch('matplotlib.pyplot.savefig', side_effect=None)

    return GenerateScoresHistograms(
        ['1'], histogram_info_by_chunks, chunk_size=3)


@pytest.fixture
def generate_histograms_with_start_end(
        mocker, score_files_with_start_end, histogram_info_with_start_end):
    mocker.patch('pandas.read_csv',
                 side_effect=lambda _, usecols, sep, header, chunksize,
                 low_memory: score_files_with_start_end.pop(0))
    mocker.patch('matplotlib.pyplot.savefig', side_effect=None)

    return GenerateScoresHistograms(
        ['1'], histogram_info_with_start_end, chunk_size=3, start='start',
        end='end')


def test_generate_histogram(mocker, generate_histograms, expected_output):
    generate_histograms.generate_scores_histograms()

    assert output[0].getvalue() == expected_output[0]
    assert output[1].getvalue() == expected_output[1]
    # assert output[2].getvalue() == expected_output[2]


def test_generate_histogram_by_chunks(
        mocker, generate_histograms_by_chunks, expected_output):
    generate_histograms_by_chunks.generate_scores_histograms()

    assert output_by_chunks[0].getvalue() == expected_output[0]
    assert output_by_chunks[1].getvalue() == expected_output[1]
    # assert output_by_chunks[2].getvalue() == expected_output[2]


def test_generate_histogram_with_start_end(
        mocker, generate_histograms_with_start_end,
        expected_output_with_start_end):
    generate_histograms_with_start_end.generate_scores_histograms()

    assert output_with_start_end[0].getvalue() ==\
        expected_output_with_start_end[0]
    assert output_with_start_end[1].getvalue() ==\
        expected_output_with_start_end[1]
    # assert output_with_start_end[2].getvalue() ==\
    #     expected_output_with_start_end[2]


@pytest.fixture
def values():
    return pd.DataFrame({'SCORE': [1, 2, 3, 4, 4, 5, 6],
                         'length': [1, 1, 1, 1, 1, 1, 1],
                         'start': [1, 2, 3, 4, 5, 6, 7],
                         'end': [1, 3, 3, 6, 10, 6, 7]})


@pytest.fixture
def bins():
    return np.array([1.0, 2.0, 3.0, 4.0, 5.0, 6.0])


@pytest.fixture
def bars(bins):
    return np.zeros(len(bins) - 1)


@pytest.fixture
def expected_bars():
    return np.array([1.0, 1.0, 1.0, 2.0, 2.0])


@pytest.fixture
def length():
    return np.array([1, 2, 1, 3, 6, 1, 1])


def test_get_variant_length(generate_histograms, values, length):
    generate_histograms.start = 'start'
    generate_histograms.end = 'end'

    variant_length = generate_histograms.get_variant_length(values)['length']

    assert np.array_equal(variant_length, length)


def test_get_empty_bars_and_bins(
        generate_histograms, histogram_info_1, bars, bins):
    histogram_info_1.bin_range = (1.0, 6.0)

    empty_bars, empty_bins =\
        generate_histograms.get_empty_bars_and_bins(histogram_info_1)

    assert np.array_equal(empty_bars, bars)
    assert np.array_equal(empty_bins, bins)


def test_fill_bars(
        generate_histograms, histogram_info_1, values, bars, bins,
        expected_bars):
    histogram_info_1.bin_range = (1.0, 6.0)

    fill_bars = generate_histograms.fill_bars(
        histogram_info_1, values, bars, bins)

    assert np.array_equal(fill_bars, expected_bars)


def test_np_histogram(values, bars, bins, expected_bars):
    fill_bars, fill_bins = np.histogram(
        values['SCORE'].values, bins=bins, range=(1.0, 6.0))

    assert np.array_equal(fill_bars, expected_bars)
    assert np.array_equal(fill_bins, bins)
