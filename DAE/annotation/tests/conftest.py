import pytest
from annotation.tools.file_io import IOManager, IOType
from box import Box
from .utils import relative_to_this_test_folder


@pytest.fixture
def variants_io(request):

    def build(fixture_name):
        io_config = {
            "infile": relative_to_this_test_folder(fixture_name),
            "outfile": "-",
        }
        io_config = Box(io_config, default_box=True, default_box_attr=None)
        io_manager = IOManager(io_config, IOType.TSV, IOType.TSV)
        return io_manager
    return build
