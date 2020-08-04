import os
import pytest

from dae.configuration.gpf_config_parser import FrozenBox
from dae.annotation.tools.file_io import (
    TSVReader,
    TSVGzipReader,
    TabixReaderVariants,
)

from .conftest import relative_to_this_test_folder


@pytest.mark.parametrize(
    "filename,header,no_header,linecount",
    [
        ("fixtures/input3.tsv.gz", ["CHROM", "POS", "REF", "ALT"], None, 20),
        (
            "fixtures/TEST3phyloP100way/TEST3phyloP100way.bedGraph.gz",
            ["0", "1", "2", "3"],
            True,
            18,
        ),
        (
            "fixtures/TEST3phastCons100way/TEST3phastCons100way.bedGraph.gz",
            ["0", "1", "2", "3"],
            True,
            19,
        ),
        (
            "fixtures/TEST3CADD/TEST3whole_genome_SNVs.tsv.gz",
            ["0", "1", "2", "3", "4", "5"],
            True,
            54,
        ),
    ],
)
def test_tsv_gzip_reader(filename, header, no_header, linecount):
    infilename = relative_to_this_test_folder(filename)
    os.path.exists(infilename)

    options = FrozenBox({"region": None, "no_header": no_header})

    with TSVGzipReader(options, filename=infilename) as reader:
        assert reader is not None
        print(reader.schema.col_names)
        assert reader.schema.col_names == header

        for line in reader.lines_read_iterator():
            print(line)
        assert reader.linecount == linecount


@pytest.mark.parametrize(
    "filename,header,linecount",
    [
        ("fixtures/input.tsv", ["id", "location", "variant"], 4),
        ("fixtures/input2.tsv", ["CHROM", "POS", "REF", "ALT"], 5),
    ],
)
def test_tsv_reader(filename, header, linecount):
    infilename = relative_to_this_test_folder(filename)
    os.path.exists(infilename)

    options = FrozenBox({"region": None, "no_header": None})

    with TSVReader(options, filename=infilename) as reader:
        assert reader is not None
        print(reader.schema.col_names)
        assert reader.schema.col_names == header

        for line in reader.lines_read_iterator():
            print(line)
        assert reader.linecount == linecount


@pytest.mark.parametrize(
    "filename,header,no_header,region,linecount",
    [
        (
            "fixtures/input3.tsv.gz",
            ["CHROM", "POS", "REF", "ALT"],
            None,
            None,
            20,
        ),
        (
            "fixtures/input3.tsv.gz",
            ["CHROM", "POS", "REF", "ALT"],
            None,
            "chr1:20002-20004",
            3,
        ),
        (
            "fixtures/input3.tsv.gz",
            ["CHROM", "POS", "REF", "ALT"],
            None,
            "chr2:20002-20005",
            4,
        ),
        (
            "fixtures/input3.tsv.gz",
            ["CHROM", "POS", "REF", "ALT"],
            None,
            "1:20002-20004",
            3,
        ),
        (
            "fixtures/input3.tsv.gz",
            ["CHROM", "POS", "REF", "ALT"],
            None,
            "2:20002-20005",
            4,
        ),
        (
            "fixtures/TEST3phyloP100way/TEST3phyloP100way.bedGraph.gz",
            ["0", "1", "2", "3"],
            True,
            None,
            18,
        ),
        (
            "fixtures/TEST3phyloP100way/TEST3phyloP100way.bedGraph.gz",
            ["0", "1", "2", "3"],
            True,
            "1:20002-20004",
            3,
        ),
        (
            "fixtures/TEST3phyloP100way/TEST3phyloP100way.bedGraph.gz",
            ["0", "1", "2", "3"],
            True,
            "2:20002-20005",
            4,
        ),
        (
            "fixtures/TEST3phyloP100way/TEST3phyloP100way.bedGraph.gz",
            ["0", "1", "2", "3"],
            True,
            "chr1:20002-20004",
            3,
        ),
        (
            "fixtures/TEST3phyloP100way/TEST3phyloP100way.bedGraph.gz",
            ["0", "1", "2", "3"],
            True,
            "chr2:20002-20005",
            4,
        ),
        (
            "fixtures/TEST3phastCons100way/TEST3phastCons100way.bedGraph.gz",
            ["0", "1", "2", "3"],
            True,
            None,
            19,
        ),
        (
            "fixtures/TEST3phastCons100way/TEST3phastCons100way.bedGraph.gz",
            ["0", "1", "2", "3"],
            True,
            "1:20002-20004",
            3,
        ),
        (
            "fixtures/TEST3phastCons100way/TEST3phastCons100way.bedGraph.gz",
            ["0", "1", "2", "3"],
            True,
            "2:20002-20005",
            3,
        ),
        (
            "fixtures/TEST3phastCons100way/TEST3phastCons100way.bedGraph.gz",
            ["0", "1", "2", "3"],
            True,
            "chr1:20002-20004",
            3,
        ),
        (
            "fixtures/TEST3phastCons100way/TEST3phastCons100way.bedGraph.gz",
            ["0", "1", "2", "3"],
            True,
            "chr2:20002-20005",
            3,
        ),
        (
            "fixtures/TEST3CADD/TEST3whole_genome_SNVs.tsv.gz",
            ["0", "1", "2", "3", "4", "5"],
            True,
            None,
            54,
        ),
        (
            "fixtures/TEST3CADD/TEST3whole_genome_SNVs.tsv.gz",
            ["0", "1", "2", "3", "4", "5"],
            True,
            "1:20002-20004",
            9,
        ),
        (
            "fixtures/TEST3CADD/TEST3whole_genome_SNVs.tsv.gz",
            ["0", "1", "2", "3", "4", "5"],
            True,
            "2:20002-20005",
            12,
        ),
        (
            "fixtures/TEST3CADD/TEST3whole_genome_SNVs.tsv.gz",
            ["0", "1", "2", "3", "4", "5"],
            True,
            "chr1:20002-20004",
            9,
        ),
        (
            "fixtures/TEST3CADD/TEST3whole_genome_SNVs.tsv.gz",
            ["0", "1", "2", "3", "4", "5"],
            True,
            "chr2:20002-20005",
            12,
        ),
    ],
)
def test_tabix_reader(filename, header, no_header, region, linecount):
    infilename = relative_to_this_test_folder(filename)
    os.path.exists(infilename)

    options = FrozenBox(
        {"region": region, "no_header": no_header}
    )

    with TabixReaderVariants(options, filename=infilename) as reader:
        assert reader is not None
        print(reader.schema.col_names)
        assert reader.schema.col_names == header

        for line in reader.lines_read_iterator():
            print(line)
        assert reader.linecount == linecount


def test_tabix_reader_simple():
    filename, header, region, linecount = (
        "fixtures/input3.tsv.gz",
        ["CHROM", "POS", "REF", "ALT"],
        None,
        20,
    )

    infilename = relative_to_this_test_folder(filename)
    os.path.exists(infilename)

    options = FrozenBox({"region": region})

    with TabixReaderVariants(options, filename=infilename) as reader:
        assert reader is not None
        print(reader.schema.col_names)
        assert reader.schema.col_names == header

        for line in reader.lines_read_iterator():
            print(line)
        assert reader.linecount == linecount
