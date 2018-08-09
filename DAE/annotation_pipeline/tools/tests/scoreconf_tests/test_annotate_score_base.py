import pytest
from copy import deepcopy
from StringIO import StringIO

from annotation_pipeline.tools.annotate_score_base \
        import ScoreAnnotator, gzip
import config
import input_output
from annotation_pipeline.annotation_pipeline import MyConfigParser


def fake_exists(filename):
    return True


def fake_gzip_open(filename, *args):
    return filename


@pytest.fixture
def mocker(mocker):
    mocker.patch.object(gzip, 'open', new=fake_gzip_open)
    mocker.patch('annotation_pipeline.tools.annotate_score_base.exists',
                 new=fake_exists)


@pytest.fixture
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


@pytest.fixture
def conf_to_dict(config_file):
    conf_parser = MyConfigParser()
    conf_parser.optionxform = str
    conf_parser.readfp(config_file)

    opts = dict(conf_parser.items('general'))
    opts_columns = {'columns': dict(conf_parser.items('columns'))}
    opts.update(opts_columns)
    return opts


@pytest.fixture
def base_config():
    return conf_to_dict(StringIO(deepcopy(config.BASE_SCORE_CONFIG)))


@pytest.fixture
def base_input():
    return StringIO(''.join(deepcopy(input_output.BASE_INPUT_FILE)))


@pytest.fixture
def base_output():
    return input_output.BASE_OUTPUT


@pytest.fixture
def base_scores():
    return StringIO(''.join(deepcopy(input_output.BASE_INPUT_SCORE)))


@pytest.fixture
def base_annotator(base_config, base_scores, mocker):
    base_opts = get_opts(c_inp='chrom', p_inp='pos',
                         file_inp=base_scores, conf_inp=base_config)
    return ScoreAnnotator(base_opts, header=['id', 'chrom', 'pos', 'variation'], search_columns=[])


def test_base_score(base_annotator, base_input, base_output, mocker):
    output = ""
    for line in base_input.readlines():
        line = line.rstrip()
        new_annotations = base_annotator.line_annotations(line.split('\t'), base_annotator.new_columns)
        for annotation in new_annotations:
            line += '\t' + annotation
        output += line + '\n'
    assert (output == base_output)
