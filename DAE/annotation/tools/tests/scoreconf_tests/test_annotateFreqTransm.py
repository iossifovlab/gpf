import pytest
import input_output
import gzip
from annotation.tools.annotateFreqTransm \
        import FrequencyAnnotator
from copy import deepcopy
from StringIO import StringIO


def get_opts(c_inp='chr', p_inp='position', x_inp=None,
             file_inp=None, direct_inp=False, config=None):
    class MockOpts:
        def __init__(self, chrom, pos, loc, score, tabix, config):
            self.c = chrom
            self.p = pos
            self.x = loc
            self.v = 'variant'
            self.H = False
            self.scores_file = score
            self.scores_config_file = config
            self.direct = tabix
            self.frequency = 'all_nParCalled,all_altFreq'
            self.labels = None
            self.default_value = ''
            self.gzip = True

    return MockOpts(c_inp, p_inp, x_inp, file_inp, direct_inp, config)


def fake_gzip_open(filename, *args):
    return filename


@pytest.fixture
def mocker(mocker):
    mocker.patch.object(gzip, 'open', new=fake_gzip_open)


@pytest.fixture
def freq_input():
    return StringIO(''.join(deepcopy(input_output.FREQ_INPUT_FILE)))


@pytest.fixture
def freq_output():
    return input_output.FREQ_OUTPUT


@pytest.fixture
def freq_scores():
    return StringIO(''.join(deepcopy(input_output.FREQ_INPUT_SCORE)))


@pytest.fixture
def freq_annotator(freq_scores, mocker):
    freq_opts = get_opts(file_inp=freq_scores)
    return FrequencyAnnotator(freq_opts,
                              header=['chr', 'position', 'variant'])


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
