import pytest
from box import Box
from annotation.tests.conftest import relative_to_this_test_folder
from annotation.tools.file_io import TSVGzipReader, \
        TabixReaderVariants, parquet_enabled
from annotation.tools.file_io_tsv import handle_chrom_prefix

if parquet_enabled:
    from annotation.tools.file_io_parquet import ParquetWriter


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
        assert handle_chrom_prefix(
                reader._has_chrom_prefix, region) == check_region

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
