
import pytest
from box import Box
from annotation.tests.utils import relative_to_this_test_folder
from annotation.tools.file_io import TabixReader


@pytest.mark.parametrize("filename", [
    "fixtures/input3.tsv.gz",
    "fixtures/input3_no_tabix_header.tsv.gz"
])
def test_tabix_reader_header(filename):
    filename = relative_to_this_test_folder(filename)

    options = Box({}, default_box=True, default_box_attr=None)

    with TabixReader(options, filename) as reader:
        assert reader is not None
        assert reader.header is not None

        assert len(reader.header) == 4
