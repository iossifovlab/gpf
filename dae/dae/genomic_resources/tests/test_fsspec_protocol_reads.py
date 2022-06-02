# pylint: disable=redefined-outer-name,C0114,C0116,protected-access

import pytest


@pytest.mark.parametrize("scheme", [
    "file",
    "s3",
    "http"
])
def test_get_all_resources(fsspec_proto, scheme):
    proto = fsspec_proto(scheme)

    resources = list(proto.get_all_resources())
    assert len(resources) == 5, resources


@pytest.mark.parametrize("scheme", [
    "file",
    "s3",
    "http"
])
def test_open_raw_file_read_three_a(fsspec_proto, scheme):
    # Given

    proto = fsspec_proto(scheme)
    res = proto.get_resource("three")

    # When
    with proto.open_raw_file(res, "sub1/a.txt") as infile:
        content = infile.read()

    # Then
    assert content == "a"


@pytest.mark.parametrize("scheme", [
    "file",
    "s3",
    "http"
])
def test_open_raw_file_read_one_compressed(fsspec_proto, scheme):
    # Given

    proto = fsspec_proto(scheme)
    res = proto.get_resource("one")

    # When
    with proto.open_raw_file(
            res, "test.txt.gz", compression="gzip") as infile:
        header = infile.readline()

    # Then
    assert header == "#chrom\tpos_begin\tpos_end\tc1\n"


@pytest.mark.parametrize("scheme", [
    "file",
    "s3",
    "http"
])
def test_open_raw_file_seek(fsspec_proto, scheme):
    # Given
    proto = fsspec_proto(scheme)
    res = proto.get_resource("xxxxx-genome")

    # When
    with proto.open_raw_file(
            res, "chr.fa") as infile:

        infile.seek(7)
        sequence = infile.read(10)

    # Then
    assert sequence == "NNACCCAAAC"


@pytest.mark.parametrize("scheme", [
    "file",
    "s3",
    "http"
])
def test_open_tabix_file_contigs(fsspec_proto, scheme):
    # Given
    proto = fsspec_proto(scheme)
    res = proto.get_resource("one")

    # When
    with proto.open_tabix_file(res, "test.txt.gz") as tabix:
        contigs = tabix.contigs

    # Then
    assert contigs == ["1", "2", "3"]


@pytest.mark.parametrize("scheme", [
    "file",
    "s3",
    "http"
])
def test_open_tabix_file_fetch_all(fsspec_proto, scheme):
    # Given
    proto = fsspec_proto(scheme)
    res = proto.get_resource("one")

    # When
    lines = []
    with proto.open_tabix_file(res, "test.txt.gz") as tabix:

        for line in tabix.fetch():
            lines.append(line)

    # Then
    assert len(lines) == 5


@pytest.mark.parametrize("scheme", [
    "file",
    "s3",
    "http"
])
def test_open_tabix_file_fetch_region(fsspec_proto, scheme):
    # Given
    proto = fsspec_proto(scheme)
    res = proto.get_resource("one")

    # When
    lines = []
    with proto.open_tabix_file(res, "test.txt.gz") as tabix:

        for line in tabix.fetch("3"):
            lines.append(line)

    # Then
    assert lines == ["3\t1\t10\t3.0", "3\t11\t20\t3.5"]
