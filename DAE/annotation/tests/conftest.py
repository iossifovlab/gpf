import pytest
import os

import pandas as pd
from builtins import str
from io import StringIO

from box import Box
from annotation.tools.file_io import IOManager, IOType


def relative_to_this_test_folder(path):
    return os.path.join(
        os.path.dirname(os.path.realpath(__file__)),
        path
    )


@pytest.fixture
def variants_io(request):

    def build(fixture_name, options=Box({})):
        io_options = options.to_dict()
        io_config = {
            "infile": relative_to_this_test_folder(fixture_name),
            "outfile": "-",
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
        df = pd.read_csv(infile, sep="\t")
        return df
    return build
