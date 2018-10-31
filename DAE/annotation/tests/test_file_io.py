
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

    with TabixReader(options, filename) as reader:
        assert reader is not None
        assert reader.header is not None

        assert reader._has_chrom_prefix == has_prefix
        assert reader._handle_chrom_prefix(region) == check_region

        count = 0
        for _line in reader.lines_read_iterator():
            count += 1
        assert count == total_count
