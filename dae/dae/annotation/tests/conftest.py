import pytest
import os

import pandas as pd
from io import StringIO

from dae.configuration.gpf_config_parser import GPFConfigParser
from dae.annotation.tools.file_io import IOManager, IOType
from dae.annotation.tools.score_file_io import ScoreFile, TabixAccess


def relative_to_this_test_folder(path):
    return os.path.join(
        os.path.dirname(os.path.realpath(__file__)),
        path
    )


@pytest.fixture(scope='session')
def work_dir():
    return relative_to_this_test_folder('fixtures')


@pytest.fixture
def variants_io(request):

    def build(fixture_name, options=None):
        if options:
            io_options = dict(options.field_values_iterator())
        else:
            io_options = dict()
        io_config = {
            'infile': relative_to_this_test_folder(fixture_name),
            'outfile': '-',
        }
        io_options.update(io_config)
        io_options = GPFConfigParser._dict_to_namedtuple(io_options)
        io_manager = IOManager(io_options, IOType.TSV, IOType.TSV)
        return io_manager
    return build


@pytest.fixture
def expected_df():
    def build(data):
        infile = StringIO(str(data))
        df = pd.read_csv(infile, sep='\t')
        return df
    return build


@pytest.fixture
def score_file():
    score_filename = relative_to_this_test_folder(
        'fixtures/TESTphastCons100way/TESTphastCons100way.bedGraph.gz')

    score_file_instance = ScoreFile(score_filename)
    assert score_file_instance is not None
    assert isinstance(score_file_instance.accessor, TabixAccess)
    return score_file_instance
