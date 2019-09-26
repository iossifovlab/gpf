import pytest
import os

import pandas as pd
from io import StringIO

from box import Box

from dae.gpf_instance.gpf_instance import GPFInstance

from dae.configuration.dae_config_parser import DAEConfigParser

from dae.annotation.tools.file_io import IOManager, IOType
from dae.annotation.tools.score_file_io import ScoreFile, TabixAccess


def relative_to_this_test_folder(path):
    return os.path.join(
        os.path.dirname(os.path.realpath(__file__)),
        path
    )


@pytest.fixture(scope='function')
def dae_config_fixture():
    return DAEConfigParser.read_and_parse_file_configuration(
        work_dir=relative_to_this_test_folder('fixtures')
    )


@pytest.fixture(scope='function')
def mocked_gpf_instance(mocker, mock_genomes_db, dae_config_fixture):
    mocker.patch('dae.gpf_instance.gpf_instance.GPFInstance')

    gpf_instance = GPFInstance()
    gpf_instance.dae_config = dae_config_fixture

    return gpf_instance


@pytest.fixture(scope='function')
def mocked_genomes_db(mocked_gpf_instance):
    return mocked_gpf_instance.genomes_db


@pytest.fixture
def variants_io(request):

    def build(fixture_name, options=Box({})):
        io_options = options.to_dict()
        io_config = {
            'infile': relative_to_this_test_folder(fixture_name),
            'outfile': '-',
        }
        io_options.update(io_config)

        io_options = Box(io_options, default_box=True, default_box_attr=None)
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
