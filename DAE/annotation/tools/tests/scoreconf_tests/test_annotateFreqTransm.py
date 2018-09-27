from __future__ import unicode_literals
import pytest
import pysam
import gzip
from annotation.tools.annotateFreqTransm import FrequencyAnnotator
from io import StringIO
from box import Box
from utils import Dummy_tbi, dummy_gzip_open


def get_opts(score_file):
    options = {
        'c': 'chr',
        'p': 'position',
        'v': 'variant',
        'H': False,
        'scores_file': score_file,
        'direct': False,
        'frequency': 'all.altFreq'
    }
    return Box(options, default_box=True, default_box_attr=None)


@pytest.fixture
def mocker(mocker):
    mocker.patch.object(pysam, 'Tabixfile', new=Dummy_tbi)
    mocker.patch.object(gzip, 'open', new=dummy_gzip_open)


@pytest.fixture
def freq_input():
    return [
        ['1', '69428', 'sub(T->G)'],
        ['1', '69438', 'sub(T->C)'],
        ['1', '69458', 'sub(T->C)'],
        ['1', '69511', 'sub(A->G)']
    ]


@pytest.fixture
def expected_annotations():
    return [['0.49'], ['0.03'], ['0.03'], ['98.00']]


@pytest.fixture
def freq_scores():
    return ('#chr\tposition\tvariant\tall.nParCalled\tall.prcntParCalled\tall.nAltAlls\tall.altFreq\tsegDups\tHW\tSSC-freq\tEVS-freq\tE65-freq\n'
            '1\t69428\tsub(T->G)\t1336\t27.03\t13\t0.49\t2\t0.0161\t0.49\t3.06\t2.47\n'
            '1\t69438\tsub(T->C)\t1430\t28.94\t1\t0.03\t2\t1.0000\t0.03\t\t0.00\n'
            '1\t69458\tsub(T->C)\t1460\t29.54\t1\t0.03\t2\t1.0000\t0.03\t\t\n'
            '1\t69511\tsub(A->G)\t300\t6.07\t588\t98.00\t2\t0.0000\t98.00\t75.98\t94.02\n')


@pytest.fixture
def freq_annotator(freq_scores, mocker):
    freq_opts = get_opts(score_file=StringIO(freq_scores))
    return FrequencyAnnotator(freq_opts,
                              header=['chr', 'position', 'variant'])


def test_freq_score(freq_input, expected_annotations, freq_annotator, mocker):
    annotations = [freq_annotator.line_annotations(line, freq_annotator.new_columns) for line in freq_input]

    assert (annotations == expected_annotations)
