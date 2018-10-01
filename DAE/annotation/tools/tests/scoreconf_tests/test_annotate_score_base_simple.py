from __future__ import unicode_literals
import pytest
import pysam
from os import remove
from io import StringIO
from utils import Dummy_tbi, dummy_gzip_open, to_file, get_opts
from annotation.tools.annotate_score_base import ScoreAnnotator, gzip, conf_to_dict


@pytest.fixture(autouse=True)
def mock(mocker):
    mocker.patch.object(pysam, 'Tabixfile', new=Dummy_tbi)
    mocker.patch.object(gzip, 'open', new=dummy_gzip_open)


@pytest.fixture
def config():
    conf = ('[general]\n'
            'header=id,chrom,starting_pos,variant,scoreValue\n'
            'noScoreValue=-100\n'
            '[columns]\n'
            'chr=chrom\n'
            'pos_begin=starting_pos\n'
            'score=scoreValue\n')
    return StringIO(conf)


@pytest.fixture
def input_():
    return [['1', '4', '4372372973', 'sub(A->C)'],
            ['5', '10', '4372372973', 'sub(G->A)'],
            ['3', 'X', '4372', 'ins(AAA)'],
            ['6', 'Y', '4372372973', 'del(2)']]


@pytest.fixture
def expected_annotations():
    return [['0.214561'], ['1.410786'], ['2.593045'], ['3.922039']]


@pytest.fixture
def scores():
    score_ = ('1\t4\t4372372973\tsub(A->C)\t0.214561\n'
              '5\t10\t4372372973\tsub(G->A)\t1.410786\n'
              '3\tX\t4372\tins(AAA)\t2.593045\n'
              '6\tY\t4372372973\tdel(2)\t3.922039\n')
    return StringIO(score_)


@pytest.fixture
def annotator(config, scores):
    opts = get_opts(scores, conf_to_dict(config))
    return ScoreAnnotator(opts,
                          header=['id', 'chrom', 'pos', 'variation'])


@pytest.fixture
def annotator_file(config, scores):
    opts = get_opts(scores, to_file(config.read()))
    yield ScoreAnnotator(opts,
                         header=['id', 'chrom', 'pos', 'variation'])
    remove(opts.scores_config_file)


def test_base_simple_dictconf(annotator, input_, expected_annotations):
    annotations = [annotator.line_annotations(line, annotator.new_columns) for line in input_]
    assert (annotations == expected_annotations)


def test_base_simple_fileconf(annotator_file, input_, expected_annotations):
    annotations = [annotator_file.line_annotations(line, annotator_file.new_columns) for line in input_]
    assert (annotations == expected_annotations)
