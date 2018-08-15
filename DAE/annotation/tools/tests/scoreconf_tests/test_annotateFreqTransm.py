import pytest
import input_output
import config
import gzip
from annotation.tools.annotateFreqTransm \
        import FrequencyAnnotator
from annotation.annotation_pipeline import MyConfigParser
from copy import deepcopy
from StringIO import StringIO


def get_opts(c_inp=None, p_inp=None, x_inp=None,
             file_inp=None, direct_inp=False, config=None):
    class MockOpts:
        def __init__(self, chrom, pos, loc, score, tabix, config):
            self.c = chrom
            self.p = pos
            self.x = loc
            self.v = 'variation'
            self.H = False
            self.scores_file = score
            self.scores_config_file = config
            self.direct = tabix
            self.labels = None

    return MockOpts(c_inp, p_inp, x_inp, file_inp, direct_inp, config)


def fake_gzip_open(filename, *args):
    return filename


def conf_to_dict(config_file):
    conf_parser = MyConfigParser()
    conf_parser.optionxform = str
    conf_parser.readfp(config_file)

    opts = dict(conf_parser.items('general'))
    opts_columns = {'columns': dict(conf_parser.items('columns'))}
    opts.update(opts_columns)
    return opts


@pytest.fixture
def mocker(mocker):
    mocker.patch.object(gzip, 'open', new=fake_gzip_open)


@pytest.fixture
def freq_input():
    return StringIO(''.join(deepcopy(input_output.BASE_INPUT_FILE)))


@pytest.fixture
def freq_output():
    return input_output.BASE_OUTPUT


@pytest.fixture
def freq_scores():
    return StringIO(''.join(deepcopy(input_output.BASE_INPUT_SCORE)))


@pytest.fixture
def freq_config():
    return conf_to_dict(StringIO(deepcopy(config.FREQ_SCORE_CONFIG)))


@pytest.fixture
def freq_annotator(freq_scores, freq_config, mocker):
    print(freq_config)
    freq_opts = get_opts(c_inp='chrom', p_inp='pos',
                         file_inp=freq_scores, config=freq_config)
    return FrequencyAnnotator(freq_opts,
                              header=['id', 'chrom', 'pos', 'variation'])


def test_freq_score(freq_input, freq_output, freq_annotator, mocker):
    output = ""
    for line in freq_input.readlines():
        line = line.rstrip()
        new_annotations = freq_annotator.line_annotations(
                          line.split('\t'),
                          freq_annotator.new_columns)
        for annotation in new_annotations:
            line += '\t' + annotation
        output += line + '\n'

    assert (output == freq_output)
