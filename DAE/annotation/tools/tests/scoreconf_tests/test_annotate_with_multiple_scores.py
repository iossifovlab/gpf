from __future__ import unicode_literals
import pytest
import os.path
import gzip
import pysam
from box import Box
from os import remove, rmdir, getcwd
from annotation.tools.annotate_with_multiple_scores \
        import MultipleScoresAnnotator
from utils import Dummy_tbi, dummy_gzip_open, to_file, get_opts


@pytest.fixture(autouse=True)
def mock(mocker):
    mocker.patch.object(pysam, 'Tabixfile', new=Dummy_tbi)
    mocker.patch.object(gzip, 'open', new=dummy_gzip_open)


@pytest.fixture
def input_():
    return ('1\t4\t4372372973\tsub(A->C)\n'
            '5\t10\t4372372973\tsub(G->A)\n'
            '3\tX\t4372\tins(AAA)\n'
            '6\tY\t4372372973\tdel(2)')


@pytest.fixture
def expected_output():
    return ('1\t4\t4372372973\tsub(A->C)\t0.214561|1234\t0.561\n'
            '5\t10\t4372372973\tsub(G->A)\t1.410786|2345\t1.786\n'
            '3\tX\t4372\tins(AAA)\t2.593045|3456\t2.045\n'
            '6\tY\t4372372973\tdel(2)\t3.922039|4567\t3.039\n')


@pytest.fixture
def score():
    return ('1\t4\t4372372973\t0.214561\t1234\n'
            '5\t10\t4372372973\t1.410786\t2345\n'
            '3\tX\t4372\t2.593045\t3456\n'
            '6\tY\t4372372973\t3.922039\t4567')


@pytest.fixture
def score2():
    return ('1\t4\t4372372973\t0.561\n'
            '5\t10\t4372372973\t1.786\n'
            '3\tX\t4372\t2.045\n'
            '6\tY\t4372372973\t3.039')


@pytest.fixture
def config():
    return ('[general]\n'
            'header=id,chrom,starting_pos,scoreValue,scoreValue2\n'
            'noScoreValue=-103\n'
            '[columns]\n'
            'chr=chrom\n'
            'pos_begin=starting_pos\n'
            'score=scoreValue,scoreValue2')


@pytest.fixture(autouse=True)
def setup_scores(score, score2, config):
    pathlist = [getcwd()+'/test_multiple_scores_tmpdir',
                getcwd()+'/test_multiple_scores_tmpdir/score1',
                getcwd()+'/test_multiple_scores_tmpdir/score2']
    for path in pathlist:
        os.mkdir(path)
    files = [to_file(score, 'score1.gz', pathlist[1]), to_file(config, 'score1.gz.conf', pathlist[1]),
             to_file(score2, 'score2.gz', pathlist[2]), to_file(config.replace(',scoreValue2', ''), 'score2.gz.conf', pathlist[2])]
    yield files
    for file_ in files:
        remove(file_)
    for dir_ in pathlist[::-1]:
        rmdir(dir_)


def test_multi_score(input_, expected_output):
    annotator = MultipleScoresAnnotator(get_opts(), header=['id', 'chrom', 'pos', 'variant'])
    output = ""
    for line in input_.split('\n'):
        line = line.split('\t')
        annotation = '\t'.join(annotator.line_annotations(line, annotator.new_columns))
        output += '\t'.join(line) + '\t' + annotation + '\n'
    assert (output == expected_output)
