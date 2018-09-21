from __future__ import unicode_literals
import pytest
import annotation.tools.file_io as file_io
from io import StringIO
from box import Box


def dummy_open(file_inp, *args):
    return file_inp


def dummy_assert(file_inp, *args):
    return True


@pytest.fixture(autouse=True)
def mock(mocker):
    mocker.patch.object(file_io, 'open', dummy_open)
    mocker.patch.object(file_io, 'assert_file_exists', dummy_assert)


def get_opts(input_, output):
    options = {
        'infile': input_,
        'outfile': output,
        'no_header': False
    }
    return Box(options, default_box=True, default_box_attr=None)


def input_base():
    return (
        '#col1\t#col2\t#col3\t#col4\t#col5\n'
        'entryOne\tentryTwo\tentryThree\tentryPreFinal\tentryFinal\n'
        'entryOne\tentryTwo\tentryThree\tentryFollowedByEmptyEntry\t\n'
        '1.3552\t64423.23423\t.,!@#$%^&*()_+-=[]{}|""/\\<>~`\tplaceholder\tCAPITALLETTERS\n'
        'placeholder\tcol3and4willbemissing\t\t\tplaceholder\n')


def test_tsv_io():
    input_buffer = StringIO(input_base())
    output_buffer = StringIO()
    options = get_opts(input_buffer, output_buffer)
    with file_io.IOManager(options, file_io.IOType.TSV, file_io.IOType.TSV) as io:
        io.line_write(io.header)
        for line in io.lines_read():
            io.line_write(line)
        assert str(output_buffer.getvalue()) == input_base()[1:]
