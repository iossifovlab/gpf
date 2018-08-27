import pytest
import config
import input_output
import os.path
import gzip
from os import remove, rmdir, mkdir
from annotation.tools.annotate_with_multiple_scores \
        import MultipleScoresAnnotator
from copy import deepcopy
from StringIO import StringIO


def get_opts(c_inp=None, p_inp=None, x_inp=None,
             dir_inp=None,
             direct_inp=False):
    class MockOpts:
        def __init__(self, chrom, pos, loc, scoredir, tabix):
            self.c = chrom
            self.p = pos
            self.x = loc
            self.H = False
            self.scores_directory = scoredir
            self.direct = tabix
            self.labels = None
            self.explicit = True
            self.scores = 'score1,score2'
            self.gzip = False

    return MockOpts(c_inp, p_inp, x_inp, dir_inp, direct_inp)


def to_file(content, name, where=None):
    if where is None:
        where = os.path.dirname('.')
    name = where + '/' + name
    temp = open(name, 'w')
    temp.write(content)
    temp.seek(0)
    temp.close()
    return temp


def setup_scoredirs():
    pathlist = [os.path.abspath('.')+'/masterdir',
                os.path.abspath('.')+'/masterdir/score1',
                os.path.abspath('.')+'/masterdir/score2']
    os.mkdir(pathlist[0])
    os.mkdir(pathlist[1])
    os.mkdir(pathlist[2])
    return pathlist


def setup_score(score, conf, name, path):
    return [to_file(score, name, path), to_file(conf, name+'.conf', path)]


def cleanup(dirs, files):
    for tmpfile in files:
        remove(tmpfile)
    for tmpdir in dirs[::-1]:
        rmdir(tmpdir)


def fake_gzip_open(filename, *args):
    return open(filename, 'r')


@pytest.fixture
def mocker(mocker):
    mocker.patch.object(gzip, 'open', new=fake_gzip_open)


@pytest.fixture
def multi_config():
    return [StringIO(deepcopy(config.MULTI_SCORE_CONFIG)),
            StringIO(deepcopy(config.MULTI_SCORE_ALT_CONFIG))]


@pytest.fixture
def multi_input():
    return StringIO(''.join(deepcopy(input_output.BASE_INPUT_FILE)))


@pytest.fixture
def multi_output():
    return input_output.MULTI_OUTPUT


@pytest.fixture
def multi_scores():
    return [StringIO(''.join(deepcopy(input_output.MULTI_INPUT_SCORE))),
            StringIO(''.join(deepcopy(input_output.MULTI_INPUT_SCORE_ALT)))]


def multi_annotator(masterdir):
    multi_opts = get_opts(c_inp='chrom', p_inp='pos',
                          dir_inp=masterdir)
    return MultipleScoresAnnotator(multi_opts,
                                   header=['id', 'chrom', 'pos', 'variation'])


def test_multi_score(multi_input, multi_scores, multi_config, multi_output, mocker):
    tmp_dirs = setup_scoredirs()

    score1 = setup_score(multi_scores[0].getvalue(),
                         config.MULTI_SCORE_CONFIG.lstrip(),
                         'score1', tmp_dirs[1])
    score2 = setup_score(multi_scores[1].getvalue(),
                         config.MULTI_SCORE_ALT_CONFIG.lstrip(),
                         'score2', tmp_dirs[2])

    annotator = multi_annotator(tmp_dirs[0])
    output = ""
    for line in multi_input.readlines():
        line = line.rstrip()
        new_annotations = annotator.line_annotations(
                          line.split('\t'),
                          annotator.new_columns)
        for annotation in new_annotations:
            line += '\t' + annotation
        output += line + '\n'
    cleanup(tmp_dirs, [tmp.name for tmp in score1+score2])
    assert (output == multi_output)
