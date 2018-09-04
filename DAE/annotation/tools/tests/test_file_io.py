from __future__ import unicode_literals
import pytest
import annotation.tools.file_io as file_io
from os import remove, getcwd
from io import StringIO
from box import Box


def dummy_open(file_inp, *args):
    if isinstance(file_inp, StringIO):
        return file_inp
    else:
        return open('file_inp', *args)


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
        'no_header': False,
        'region': None
    }
    return Box(options, default_box=True, default_box_attr=None)


def input_base():
    return (
        '#col1\t#col2\t#col3\t#col4\t#col5\n'
        'entryOne\tentryTwo\tentryThree\tentryPreFinal\tentryFinal\n'
        'entryOne\tentryTwo\tentryThree\tentryFollowedByEmptyEntry\t\n'
        '1.3552\t64423.23423\t.,!@#$%^&*()_+-=[]{}|""/\\<>~`\tplaceholder\tCAPITALLETTERS\n'
        'placeholder\tcol3and4willbemissing\t\t\tplaceholder\n')


@pytest.fixture
def setup_parquet_input():
    input_buffer = StringIO(input_base())
    output_path = getcwd() + '/pqtest_buffer.parquet'
    options = get_opts(input_buffer, output_path)
    with file_io.IOManager(options, file_io.IOType.TSV, file_io.IOType.Parquet) as io:
        io.line_write(io.header)
        for line in io.lines_read():
            io.line_write(line)
    yield output_path
    remove(output_path)


def test_tsv_io():
    input_buffer = StringIO(input_base())
    output_buffer = StringIO()
    options = get_opts(input_buffer, output_buffer)
    with file_io.IOManager(options, file_io.IOType.TSV, file_io.IOType.TSV) as io:
        io.line_write(io.header)
        for line in io.lines_read():
            io.line_write(line)
        assert str(output_buffer.getvalue()) == input_base()[1:]


def test_parquet_io(setup_parquet_input):
    input_path = setup_parquet_input
    output_buffer = StringIO()
    options = get_opts(input_path, output_buffer)
    with file_io.IOManager(options, file_io.IOType.Parquet, file_io.IOType.TSV) as io:
        for line in io.lines_read():
            io.line_write(line)
        assert str(output_buffer.getvalue()) == input_base()[1:]
