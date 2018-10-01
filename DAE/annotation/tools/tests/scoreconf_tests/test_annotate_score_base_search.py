from __future__ import unicode_literals
import pytest
import pysam
from io import StringIO
from utils import Dummy_tbi, dummy_gzip_open, get_opts
from annotation.tools.annotate_score_base import ScoreAnnotator, gzip, conf_to_dict


@pytest.fixture(autouse=True)
def mock(mocker):
    mocker.patch.object(pysam, 'Tabixfile', new=Dummy_tbi)
    mocker.patch.object(gzip, 'open', new=dummy_gzip_open)


@pytest.fixture
def config():
    conf = ('[general]\n'
            'header=id,chrom,starting_pos,ending_pos,marker,scoreValue\n'
            'noScoreValue=-102\n'
            '[columns]\n'
            'chr=chrom\n'
            'pos_begin=starting_pos\n'
            'pos_end=ending_pos\n'
            'score=scoreValue\n'
            'search=marker\n')
    return StringIO(conf)


@pytest.fixture
def input_():
    return [['1', '4', '4372372973', '4372372973', 'sub(A->C)', '2'],
            ['3', 'X', '4372', '4374', 'ins(AAA)', '2']]


@pytest.fixture
def expected_annotations():
    return [[[0.56789]], [[2.4567]]]


@pytest.fixture
def scores():
    score_ = ('1\t4\t4372372973\t4372372973\t2\t0.56789\n'
              '5\t10\t4372372973\t4372372973\t1\t1.5678\n'
              '3\tX\t4372\t4374\t2\t2.4567\n'
              '6\tY\t4372372973\t4372372974\t1\t3.7890\n')
    return StringIO(score_)


@pytest.fixture
def annotator(config, scores):
    opts = get_opts(scores, conf_to_dict(config), search_cols=['marker'])
    return ScoreAnnotator(opts, header=['id', 'chrom', 'pos', 'ending_pos', 'variation', 'marker'])


def test_search_score(annotator, input_, expected_annotations):
    annotations = [annotator.line_annotations(line, annotator.new_columns) for line in input_]
    assert (annotations == expected_annotations)
