# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pytest

from dae.genomic_resources.testing import \
    build_s3_test_protocol, build_http_test_protocol, \
    build_filesystem_test_protocol, setup_directories, setup_vcf, setup_tabix


@pytest.fixture(scope="module", params=["file", "http", "s3"])
def fsspec_proto(request, content_fixture, tmp_path_factory):

    root_path = tmp_path_factory.mktemp("fsspec_proto")
    setup_directories(root_path, content_fixture)
    setup_tabix(
        root_path / "one" / "test.txt.gz",
        """
            #chrom  pos_begin  pos_end    c1
            1      1          10         1.0
            2      1          10         2.0
            2      11         20         2.5
            3      1          10         3.0
            3      11         20         3.5
        """,
        seq_col=0, start_col=1, end_col=2)

    setup_vcf(
        root_path / "one" / "in.vcf.gz",
        """
        ##fileformat=VCFv4.2
        ##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">
        ##contig=<ID=foo>
        ##contig=<ID=bar>
        #CHROM POS ID REF ALT QUAL FILTER INFO FORMAT m1
        foo    10  .  T   G     .    .      .    GT   0/1
        foo    13  .  T   G     .    .      .    GT   0/1
        bar    15  .  T   G     .    .      .    GT   1/1
        bar    16  .  T   G     .    .      .    GT   0/1
        """)
    scheme = request.param
    if scheme == "file":
        yield build_filesystem_test_protocol(root_path)
        return
    if scheme == "http":
        with build_http_test_protocol(root_path) as proto:
            yield proto
        return
    if scheme == "s3":
        with build_s3_test_protocol(root_path) as proto:

            yield proto

        return

    raise ValueError(f"unexpected protocol scheme: <{scheme}>")


def test_get_all_resources(fsspec_proto):
    proto = fsspec_proto
    resources = list(proto.get_all_resources())
    assert len(resources) == 5, resources


def test_open_raw_file_read_three_a(fsspec_proto):
    # Given
    proto = fsspec_proto
    res = proto.get_resource("three")

    # When
    with proto.open_raw_file(res, "sub1/a.txt") as infile:
        content = infile.read()

    # Then
    assert content == "a"


def test_open_raw_file_read_one_compressed(fsspec_proto):
    # Given
    proto = fsspec_proto
    res = proto.get_resource("one")

    # When
    with proto.open_raw_file(
            res, "test.txt.gz", compression="gzip") as infile:
        header = infile.readline()

    # Then
    assert header == "#chrom\tpos_begin\tpos_end\tc1\n"


def test_open_raw_file_seek(fsspec_proto):
    # Given
    proto = fsspec_proto
    res = proto.get_resource("xxxxx-genome")

    # When
    with proto.open_raw_file(
            res, "chr.fa") as infile:

        infile.seek(7)
        sequence = infile.read(10)

    # Then
    assert sequence == "NNACCCAAAC"


def test_open_tabix_file_contigs(fsspec_proto):
    # Given
    proto = fsspec_proto
    res = proto.get_resource("one")

    # When
    with proto.open_tabix_file(res, "test.txt.gz") as tabix:
        contigs = tabix.contigs

    # Then
    assert contigs == ["1", "2", "3"]


def test_open_tabix_file_fetch_all(fsspec_proto):
    # Given
    proto = fsspec_proto
    res = proto.get_resource("one")

    # When
    lines = []
    with proto.open_tabix_file(res, "test.txt.gz") as tabix:

        for line in tabix.fetch():
            lines.append(line)

    # Then
    assert len(lines) == 5


def test_open_tabix_file_fetch_region(fsspec_proto):
    # Given
    proto = fsspec_proto
    res = proto.get_resource("one")

    # When
    lines = []
    with proto.open_tabix_file(res, "test.txt.gz") as tabix:

        for line in tabix.fetch("3"):
            lines.append(line)

    # Then
    assert lines == ["3\t1\t10\t3.0", "3\t11\t20\t3.5"]


def test_open_vcf_file_contigs(fsspec_proto):
    # Given
    proto = fsspec_proto
    res = proto.get_resource("one")
    # When
    with proto.open_vcf_file(res, "in.vcf.gz") as vcf:
        contigs = list(vcf.header.contigs)

    # Then
    assert contigs == ["foo", "bar"]


def test_open_vcf_file_fetch_all(fsspec_proto):
    # Given
    proto = fsspec_proto
    res = proto.get_resource("one")

    # When
    lines = []
    with proto.open_vcf_file(res, "in.vcf.gz") as vcf:

        for line in vcf.fetch():
            lines.append(line)

    # Then
    assert len(lines) == 4


def test_open_vcf_file_fetch_region(fsspec_proto):
    # Given
    proto = fsspec_proto
    res = proto.get_resource("one")

    # When
    lines = []
    with proto.open_vcf_file(res, "in.vcf.gz") as vcf:

        for line in vcf.fetch("foo"):
            lines.append(line)

    # Then
    assert len(lines) == 2
