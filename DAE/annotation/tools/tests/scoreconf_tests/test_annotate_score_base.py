import pytest
import config
import input_output
import tempfile
import os.path
from os import remove
from annotation.tools.annotate_score_base \
        import ScoreAnnotator, gzip, conf_to_dict
from copy import deepcopy
from StringIO import StringIO


def fake_gzip_open(filename, *args):
    return filename


@pytest.fixture
def mocker(mocker):
    mocker.patch.object(gzip, 'open', new=fake_gzip_open)


def get_opts(c_inp=None, p_inp=None, x_inp=None,
             file_inp=None, conf_inp=None, direct_inp=False):
    class MockOpts:
        def __init__(self, chrom, pos, loc, score, conf, tabix):
            self.c = chrom
            self.p = pos
            self.x = loc
            self.scores_file = score
            self.scores_config_file = conf
            self.direct = tabix
            self.labels = None

    return MockOpts(c_inp, p_inp, x_inp, file_inp, conf_inp, direct_inp)


def to_file(content, where=None):
    if where is None:
        where = os.path.dirname('.')
    temp = tempfile.NamedTemporaryFile(dir=where, delete=False)
    temp.write(content.read())
    temp.seek(0)
    return temp


@pytest.fixture
def base_config():
    return StringIO(deepcopy(config.BASE_SCORE_CONFIG))


@pytest.fixture
def full_config():
    return StringIO(deepcopy(config.FULL_SCORE_CONFIG))


@pytest.fixture
def search_config():
    return StringIO(deepcopy(config.SEARCH_SCORE_CONFIG))


@pytest.fixture
def base_input():
    return StringIO(''.join(deepcopy(input_output.BASE_INPUT_FILE)))


@pytest.fixture
def full_input():
    return StringIO(''.join(deepcopy(input_output.FULL_INPUT_FILE)))


@pytest.fixture
def search_input():
    return StringIO(''.join(deepcopy(input_output.SEARCH_INPUT_FILE)))


@pytest.fixture
def base_output():
    return input_output.BASE_OUTPUT


@pytest.fixture
def full_output():
    return input_output.FULL_OUTPUT


@pytest.fixture
def search_output():
    return input_output.SEARCH_OUTPUT


@pytest.fixture
def base_scores():
    return StringIO(''.join(deepcopy(input_output.BASE_INPUT_SCORE)))


@pytest.fixture
def full_scores():
    return StringIO(''.join(deepcopy(input_output.FULL_INPUT_SCORE)))


@pytest.fixture
def search_scores():
    return StringIO(''.join(deepcopy(input_output.SEARCH_INPUT_SCORE)))


@pytest.fixture
def base_annotator(base_config, base_scores, mocker):
    base_opts = get_opts(c_inp='chrom', p_inp='pos',
                         file_inp=base_scores,
                         conf_inp=conf_to_dict(base_config))
    return ScoreAnnotator(base_opts,
                          header=['id', 'chrom', 'pos', 'variation'],
                          search_columns=[])


@pytest.fixture
def base_annotator_file(base_config, base_scores, mocker):
    base_opts = get_opts(c_inp='chrom', p_inp='pos',
                         file_inp=base_scores,
                         conf_inp=to_file(base_config).name)
    return ScoreAnnotator(base_opts,
                          header=['id', 'chrom', 'pos', 'variation'],
                          search_columns=[])


@pytest.fixture
def full_annotator(full_config, full_scores, mocker):
    full_opts = get_opts(c_inp='chrom', p_inp='starting_pos',
                         file_inp=full_scores,
                         conf_inp=conf_to_dict(full_config))
    return ScoreAnnotator(full_opts,
                          header=['id', 'chrom', 'starting_pos', 'ending_pos', 'variation'],
                          search_columns=[])


@pytest.fixture
def search_annotator(search_config, search_scores, mocker):
    search_opts = get_opts(c_inp='chrom', p_inp='starting_pos',
                           file_inp=search_scores,
                           conf_inp=conf_to_dict(search_config))
    return ScoreAnnotator(search_opts,
                          header=['id', 'chrom', 'starting_pos', 'ending_pos', 'variation', 'marker'],
                          search_columns=['marker'])


def test_base_score(base_annotator, base_input, base_output, mocker):
    output = ""
    for line in base_input.readlines():
        line = line.rstrip()
        new_annotations = base_annotator.line_annotations(
                          line.split('\t'),
                          base_annotator.new_columns)
        for annotation in new_annotations:
            line += '\t' + annotation
        output += line + '\n'
    assert (output == base_output)


def test_base_score_file(base_annotator_file, base_input, base_output, mocker):
    output = ""
    for line in base_input.readlines():
        line = line.rstrip()
        new_annotations = base_annotator_file.line_annotations(
                          line.split('\t'),
                          base_annotator_file.new_columns)
        for annotation in new_annotations:
            line += '\t' + annotation
        output += line + '\n'
    remove(base_annotator_file.opts.scores_config_file)
    assert (output == base_output)


def test_full_score(full_annotator, full_input, full_output, mocker):
    output = ""
    for line in full_input.readlines():
        line = line.rstrip()
        new_annotations = full_annotator.line_annotations(
                          line.split('\t'),
                          full_annotator.new_columns)
        for annotation in new_annotations:
            line += '\t' + annotation
        output += line + '\n'
    assert (output == full_output)


def test_search_score(search_annotator, search_input, search_output, mocker):
    output = ""
    for line in search_input.readlines():
        line = line.rstrip()
        new_annotations = search_annotator.line_annotations(
                          line.split('\t'),
                          search_annotator.new_columns)
        for annotation in new_annotations:
            line += '\t' + annotation
        output += line + '\n'
    assert (output == search_output)
