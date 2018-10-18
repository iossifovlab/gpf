from __future__ import unicode_literals
import pytest
import gzip
import pysam
from box import Box
from io import StringIO
from os import mkdir, getcwd, remove, rmdir
from .utils import Dummy_tbi, dummy_gzip_open, to_file
from annotation.tools.add_missense_scores import MissenseScoresAnnotator


def get_opts(scorefile, conf):
    options = {
        'c': 'chrom',
        'p': 'pos',
        'r': 'ref',
        'a': 'alt',
        'H': False,
        'dbnsfp': scorefile,
        'config': conf,
        'reference_genome': 'hg19',
        'columns': 'missense',
        'direct': False,
    }
    return Box(options, default_box=True, default_box_attr=None)


@pytest.fixture(autouse=True)
def mock(mocker):
    mocker.patch.object(pysam, 'Tabixfile', new=Dummy_tbi)
    mocker.patch.object(gzip, 'open', new=dummy_gzip_open)


@pytest.fixture
def input_():
    return [['1', '1', '4372372973', 'sub(A->C)', '2', '3'],
            ['3', '1', '4372493499', 'ins(AAA)', '2', '3']]


@pytest.fixture
def expected_annotations():
    return [[[0.56789]], [[2.4567]]]


@pytest.fixture
def scores():
    return ('1\t1\t4372372973\t2\t3\t0.56789\n'
            '5\t1\t4372372975\t1\t4\t1.5678\n'
            '3\t1\t4372493499\t2\t3\t2.4567\n'
            '6\t1\t4372372974\t1\t4\t3.7890\n')


@pytest.fixture
def config():
    conf = ('[general]\n'
            'header=id,chr,pos,ref,alt,missense\n'
            'reference_genome=hg19\n'
            'noScoreValue=-104\n'
            '[columns]\n'
            'chr=chr\n'
            'pos_begin=pos\n'
            'pos_end=pos\n'
            'score=missense\n'
            'search=ref,alt\n')
    return StringIO(conf)


@pytest.fixture(autouse=True)
def setup_scores(scores):
    score_dir = getcwd() + '/test_missense_scores_tmpdir'
    mkdir(score_dir)
    score_file = to_file(scores, where=score_dir, suffix='.chr1')
    yield [score_dir, score_file]
    remove(score_file)
    rmdir(score_dir)


@pytest.fixture
def annotator(setup_scores, config):
    opts = get_opts(setup_scores[1], config)
    return MissenseScoresAnnotator(
        opts, header=['id', 'chrom', 'pos', 'variant', 'ref', 'alt'])


def test_missense_score(annotator, input_, expected_annotations):
    annotations = [
        annotator.line_annotations(line, annotator.new_columns) 
        for line in input_]
    assert (annotations == expected_annotations)
