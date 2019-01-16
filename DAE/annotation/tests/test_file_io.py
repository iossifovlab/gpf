import pytest
from box import Box
from annotation.tests.conftest import relative_to_this_test_folder
from annotation.tools.file_io import TSVGzipReader, \
        TabixReaderVariants, parquet_enabled

if parquet_enabled:
    from annotation.tools.file_io_parquet import ParquetWriter


# class Dummy_annotator(object):

#     def __init__(self):
#         pass

#     def line_annotations(self, line, score):
#         for scoreline in score:
#             if line[0] == scoreline[0]:
#                 line.append(scoreline[1])
#                 return line
#         line.append('-404')
#         return line


# def dummy_open(file_inp, mode, *args, **kwargs):
#     if isinstance(file_inp, StringIO):
#         if 'r' in mode:
#             content = file_inp.getvalue()
#             return StringIO(content)
#         elif 'w' in mode:
#             return file_inp
#     else:
#         return open('file_inp', *args, **kwargs)
# 
# 
# def dummy_assert(file_inp, *args):
#     return True


# @pytest.fixture(autouse=True)
# def mock(mocker):
#     mocker.patch.object(file_io, 'open', dummy_open)
#     mocker.patch.object(file_io, 'assert_file_exists', dummy_assert)


# def get_opts(input_, output):
#     options = {
#         'infile': input_,
#         'outfile': output,
#         'no_header': False,
#         'region': None,
#         'separator': '\t'
#     }
#     return Box(options, default_box=True, default_box_attr=None)
# 
# 
# def input_base():
#     return "".join([
#         '#col1\t#col2\t#col3\t#col4\t#col5\n'
#         'entryOne\tentryTwo\tentryThree\tentryPreFinal\tentryFinal\n'
#         'entryOneEE\tentryTwo\tentryThree\tentryFollowedByEmptyEntry\t\n'
#         '1.3552\t64423.23423\t.,!@#$%^&*()_+-=[]{}|""/\\<>~`\tplaceholder\t'
#         'CAPITALLETTERS\n'
#         'placeholder\tcol3and4willbemissing\t\t\tplaceholder\n'])
# 
# 
# 
# def expected_output():
#     return (
#         '#col1\t#col2\t#col3\t#col4\t#col5\t#score\n'
#         'entryOne\tentryTwo\tentryThree\tentryPreFinal\tentryFinal\t42\n'
#         'entryOneEE\tentryTwo\tentryThree\t'
#         'entryFollowedByEmptyEntry\t\t42\n'
#         '1.3552\t64423.23423\t.,!@#$%^&*()_+-=[]{}|""/\\<>~`\t'
#         'placeholder\tCAPITALLETTERS\t42\n'
#         'placeholder\tcol3and4willbemissing\t\t\tplaceholder\t42\n')


@pytest.mark.skipif(parquet_enabled is False,
                    reason='pyarrow module not installed')
def test_column_coercion():
    def recursive_coerce(data):
        if type(data) is list:
            return [recursive_coerce(elem) for elem in data]
        else:
            return float(data)

    col1 = [1, 2.5, 3, 'a', -5, 6, 'b']
    col4 = [['1.5', '4.3'], ['-3.4', '6.4'], ['5.0', '4.2']]
    assert ParquetWriter.coerce_column('col1', col1, str) \
        == list(map(str, col1))
    assert ParquetWriter.coerce_column('col4', col4, float) \
        == list(map(recursive_coerce, col4))


# @pytest.fixture
# def setup_parquet_input():
#     input_buffer = StringIO(input_base())
#     output_path = getcwd() + '/pqtest_buffer.parquet'
#     options = get_opts(input_buffer, output_path)
#     # annotator = Dummy_annotator()
#     with file_io.IOManager(
#             options, file_io.IOType.TSV, file_io.IOType.Parquet) as io:
#         io.line_write(io.header + ['#score'])
#         for line in io.lines_read():
#             annotated = annotator.line_annotations(line, score())
#             io.line_write(annotated)
#     yield output_path
#     remove(output_path)


# def test_tsv_io():
#     input_buffer = StringIO(input_base())
#     output_buffer = StringIO()
#     options = get_opts(input_buffer, output_buffer)
#     # annotator = Dummy_annotator()
#     with file_io.IOManager(
#             options, file_io.IOType.TSV, file_io.IOType.TSV) as io:
#         io.line_write(io.header + ['#score'])
#         for line in io.lines_read():
#             line.append(42)
#             io.line_write(line)
#         assert str(output_buffer.getvalue()) == str(expected_output())[1:]


# def test_parquet_io(setup_parquet_input):
#     input_path = setup_parquet_input
#     output_buffer = StringIO()
#     options = get_opts(input_path, output_buffer)
#     with file_io.IOManager(
#             options, file_io.IOType.Parquet, file_io.IOType.TSV) as io:
#         for line in io.lines_read():
#             io.line_write(line)
#         assert str(output_buffer.getvalue()) == str(expected_output())[1:]


@pytest.mark.parametrize("filename", [
    "fixtures/input3.tsv.gz",
    "fixtures/input3_no_tabix_header.tsv.gz"
])
def test_tabix_reader_header(filename):
    filename = relative_to_this_test_folder(filename)

    options = Box({}, default_box=True, default_box_attr=None)

    with TabixReaderVariants(options, filename) as reader:
        assert reader is not None
        assert reader.schema.col_names is not None

        assert len(reader.schema.col_names) == 4


@pytest.mark.parametrize(
    "filename,has_prefix,region,total_count,check_region",
    [
        ("fixtures/input3.tsv.gz", True, "chr2:20001-20004",
         4, "chr2:20001-20004"),
        ("fixtures/input3.tsv.gz", True, "2:20001-20004",
         4, "chr2:20001-20004"),
        ("fixtures/input4.tsv.gz", False, "2:20001-20004",
         4, "2:20001-20004"),
        ("fixtures/input4.tsv.gz", False, "chr2:20001-20004",
         4, "2:20001-20004"),
        ("fixtures/input3.tsv.gz", True, "chr3:10000-20004",
         5, "chr3:10000-20004"),
        ("fixtures/input3.tsv.gz", True, "3:10000-20004",
         5, "chr3:10000-20004"),
        ("fixtures/input4.tsv.gz", False, "3:10000-20004",
         5, "3:10000-20004"),
        ("fixtures/input4.tsv.gz", False, "chr3:10000-20004",
         5, "3:10000-20004"),
        ("fixtures/TEST3CADD/TEST3whole_genome_SNVs.tsv.gz",
         False, "3:10000-20004",
         15, "3:10000-20004"),
        ("fixtures/TEST3CADD/TEST3whole_genome_SNVs.tsv.gz",
         False, "chr3:10000-20004",
         15, "3:10000-20004"),
    ]
)
def test_tabix_chrom_prefix(
        filename, has_prefix, region, total_count, check_region):
    filename = relative_to_this_test_folder(filename)

    options = Box({
        "region": region,
    }, default_box=True, default_box_attr=None)

    with TabixReaderVariants(options, filename) as reader:
        assert reader is not None
        assert reader.schema.col_names is not None

        assert reader._has_chrom_prefix == has_prefix
        assert reader._handle_chrom_prefix(region) == check_region

        count = 0
        for _line in reader.lines_read_iterator():
            count += 1
        assert count == total_count


def test_tabix_region_strictness():
    # long_variant.vcf.gz has 6 variants before
    # the region 4:47788570 and 1 that is before it,
    # but overlaps it due to its length. We wish to omit
    # all 7 variants.

    filename = relative_to_this_test_folder('fixtures/long_variant.vcf.gz')

    options = Box({
        'vcf': True,
        'c': 'CHROM',
        'p': 'POS',
        'r': 'REF',
        'a': 'ALT',
        'region': '4:47788570',
    }, default_box=True, default_box_attr=None)

    with TSVGzipReader(options, filename) as reader:
        assert reader is not None

        all_line_count = 0
        for _line in reader.lines_read_iterator():
            all_line_count += 1

    with TabixReaderVariants(options, filename) as reader:
        assert reader is not None

        count = 0
        for _line in reader.lines_read_iterator():
            print(_line)
            count += 1
        assert (all_line_count - count) == 7
