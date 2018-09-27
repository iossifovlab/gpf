from __future__ import unicode_literals
import pytest
import input_output
import config
import gzip
import tempfile
import os
import pysam
from annotation.tools.add_missense_scores \
        import MissenseScoresAnnotator
from annotation.tools.annotate_score_base \
        import conf_to_dict
from copy import deepcopy
from io import StringIO


def to_file(content, where=None):
    if where is None:
        where = os.path.dirname('.')
    temp = tempfile.NamedTemporaryFile(dir=where, delete=False, suffix='.chr1',
        mode='w+t')
    temp.write(content)
    temp.seek(0)
    return temp


def setup_scoredir():
    dbnsfp = tempfile.mkdtemp(dir=os.path.dirname('.'))
    return dbnsfp


def get_opts(c_inp=None, p_inp=None, x_inp=None,
             dir_inp=None, direct_inp=False, config=None):
    class MockOpts:
        def __init__(self, chrom, pos, loc, scoredir, tabix, config):
            self.c = chrom
            self.p = pos
            self.x = loc
            self.H = False
            self.r = 'ref'
            self.a = 'alt'
            self.dbnsfp = scoredir
            self.config = config
            self.columns = 'missense'
            self.direct = tabix
            self.labels = None
            self.reference_genome = 'hg19'

    return MockOpts(c_inp, p_inp, x_inp, dir_inp, direct_inp, config)


def fake_gzip_open(filename, *args, **kwargs):
    return open(filename, 'r')


def cleanup(dirs, files):
    for tmpfile in files:
        os.remove(tmpfile)
    for tmpdir in dirs[::-1]:
        os.rmdir(tmpdir)


class Dummy_tbi:

    def __init__(self, filename):
        self.file = open(filename, 'r')
        self.file.readline()

    def get_splitted_line(self):
        res = self.file.readline().rstrip('\n')
        if res == '':
            return res
        else:
            return res.split('\t')

    def fetch(self, region, parser):
        return iter(self.get_splitted_line, '')


@pytest.fixture
def mocker(mocker):
    mocker.patch.object(pysam, 'Tabixfile', new=Dummy_tbi)
    mocker.patch.object(gzip, 'open', new=fake_gzip_open)


@pytest.fixture
def missense_input():
    return StringIO(''.join(deepcopy(input_output.MISSENSE_INPUT_FILE)))


@pytest.fixture
def missense_output():
    return input_output.MISSENSE_OUTPUT


@pytest.fixture
def missense_scores():
    return StringIO(''.join(deepcopy(input_output.MISSENSE_INPUT_SCORE)))


@pytest.fixture
def dbnsfp_config():
    return StringIO(deepcopy(config.DBNSFP_SCORE_CONFIG))


def missense_annotator(dbnsfp, conf_inp):
    missense_opts = get_opts(c_inp='chrom', p_inp='pos',
                             dir_inp=dbnsfp, config=conf_inp)
    return MissenseScoresAnnotator(missense_opts,
                                   header=['id', 'chrom', 'pos', 'variation', 'ref', 'alt'])


def test_missense_score(missense_input, missense_scores, missense_output,
                        dbnsfp_config, mocker):
    tmp_dir = setup_scoredir()
    dbnsfp_score = to_file(missense_scores.getvalue(), where=tmp_dir)

    annotator = missense_annotator(dbnsfp_score.name, dbnsfp_config)
    output = ""
    for line in missense_input.readlines():
        line = line.rstrip()
        new_annotations = annotator.line_annotations(
                          line.split('\t'),
                          annotator.new_columns)
        for annotation in new_annotations:
            line += '\t' + annotation
        output += line + '\n'

    cleanup([tmp_dir], [dbnsfp_score.name])
    assert (output == missense_output)
