from __future__ import unicode_literals
import pytest
import os.path
import gzip
import pysam
from os import remove, rmdir, getcwd
from annotation.tools.annotate_with_multiple_scores \
        import MultipleScoresAnnotator
from .utils import Dummy_tbi, dummy_gzip_open, to_file, \
    get_test_annotator_opts


@pytest.fixture(autouse=True)
def mock(mocker):
    mocker.patch.object(pysam, 'Tabixfile', new=Dummy_tbi)
    mocker.patch.object(gzip, 'open', new=dummy_gzip_open)


@pytest.fixture
def input_():
    return [
        ['1', '4', '4372372973', 'sub(A->C)'],
        ['5', '10', '4372372973', 'sub(G->A)'],
        ['3', 'X', '4372', 'ins(AAA)'],
        ['6', 'Y', '4372372973', 'del(2)']
    ]


@pytest.fixture
def expected_output():
    return [
        [[0.214561, 1234.0], [0.561]],
        [[1.410786, 2345.0], [1.786]],
        [[2.593045, 3456.0], [2.045]],
        [[3.922039, 4567.0], [3.039]]
    ]


@pytest.fixture
def score():
    return ('1\t4\t4372372973\t0.214561\t1234\n'
            '5\t10\t4372372973\t1.410786\t2345\n'
            '3\tX\t4372\t2.593045\t3456\n'
            '6\tY\t4372372973\t3.922039\t4567')


@pytest.fixture
def score_config():
    return ('[general]\n'
            'header=id,chrom,starting_pos,scoreValue,scoreValue2\n'
            'noScoreValue=-103\n'
            '[columns]\n'
            'chr=chrom\n'
            'pos_begin=starting_pos\n'
            'score=scoreValue,scoreValue2')


@pytest.fixture
def score2():
    return ('1\t4\t4372372973\t0.561\n'
            '5\t10\t4372372973\t1.786\n'
            '3\tX\t4372\t2.045\n'
            '6\tY\t4372372973\t3.039')


@pytest.fixture(autouse=True)
def setup_scores(score, score2, score_config):
    pathlist = [getcwd()+'/test_multiple_scores_tmpdir',
                getcwd()+'/test_multiple_scores_tmpdir/score1',
                getcwd()+'/test_multiple_scores_tmpdir/score2']
    for path in pathlist:
        os.mkdir(path)
    files = [
        to_file(score, 'score1.gz', pathlist[1]),
        to_file(score_config, 'score1.gz.conf', pathlist[1]),
        to_file(score2, 'score2.gz', pathlist[2]),
        to_file(score_config.replace(',scoreValue2', ''),
                'score2.gz.conf', pathlist[2])]
    yield files
    for file_ in files:
        remove(file_)
    for dir_ in pathlist[::-1]:
        rmdir(dir_)


def test_multi_score(input_, expected_output):
    annotator = MultipleScoresAnnotator(
        get_test_annotator_opts(), header=['id', 'chrom', 'pos', 'variant'])
    result = []
    for line in input_:
        annotation = annotator.line_annotations(line, annotator.new_columns)
        result.append(annotation)
    assert (result == expected_output)
