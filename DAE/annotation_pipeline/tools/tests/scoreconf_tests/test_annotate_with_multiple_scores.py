import pytest
import config
import input_output
import os.path
import tempfile
import gzip
from os import remove, rmdir
from annotation_pipeline.tools.annotate_with_multiple_scores \
        import MultipleScoresAnnotator
from copy import deepcopy
from StringIO import StringIO


def to_file(content, where=None):
    if where is None:
        where = os.path.dirname('.')
    temp = tempfile.NamedTemporaryFile(dir=where, delete=False, suffix='.tmp')
    temp.write(content)
    temp.seek(0)
    return temp


def get_opts(c_inp=None, p_inp=None, x_inp=None,
             dir_inp=None, scores_inp=None, confs_inp=None,
             direct_inp=False):
    class MockOpts:
        def __init__(self, chrom, pos, loc, scoredir, scores, confs, tabix):
            self.c = chrom
            self.p = pos
            self.x = loc
            self.H = False
            self.scores_directory = scoredir
            self.scores = scores
            self.scores_configs = confs
            self.direct = tabix
            self.labels = None
            self.explicit = True

    return MockOpts(c_inp, p_inp, x_inp, dir_inp, scores_inp, confs_inp, direct_inp)


def setup_scoredirs():
    master_dir = tempfile.mkdtemp(dir=os.path.dirname('.'))
    score1_dir = tempfile.mkdtemp(dir=master_dir)
    score2_dir = tempfile.mkdtemp(dir=master_dir)
    return [master_dir, score1_dir, score2_dir]


def setup_score(score, conf, path):
    return [to_file(score, path), to_file(conf, path)]


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
            StringIO(deepcopy(config.MULTI_SCORE_CONFIG))]


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


def multi_annotator(masterdir, scores, confs):
    multi_opts = get_opts(c_inp='chrom', p_inp='pos',
                          dir_inp=masterdir,
                          scores_inp=scores,
                          confs_inp=confs)
    return MultipleScoresAnnotator(multi_opts,
                                   header=['id', 'chrom', 'pos', 'variation'])


def test_multi_score(multi_input, multi_scores, multi_config, multi_output, mocker):
    tmp_dirs = setup_scoredirs()

    score1 = setup_score(multi_scores[0].getvalue(), config.MULTI_SCORE_CONFIG.lstrip(), tmp_dirs[1])
    score2 = setup_score(multi_scores[1].getvalue(), config.MULTI_SCORE_CONFIG.lstrip(), tmp_dirs[2])
    scores = ','.join([score1[0].name, score2[0].name])
    confs = ','.join([score1[1].name, score2[1].name])

    annotator = multi_annotator(tmp_dirs[0], scores, confs)
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
