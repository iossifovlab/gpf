# pylint: disable=W0621,C0114,C0116,W0212,W0613
from typing import Any, Generator

import pytest

from dae.genomic_resources.repository import \
    GR_CONF_FILE_NAME, RepositoryProtocol
from dae.genomic_resources.testing import \
    build_s3_test_protocol, build_http_test_protocol, \
    build_filesystem_test_protocol, setup_directories, setup_vcf, setup_tabix

pytestmark = [pytest.mark.grr_full, pytest.mark.grr_http]


@pytest.fixture
def tabix_fsspec_proto(
    content_fixture: dict[str, Any],
    tmp_path_factory: pytest.TempPathFactory,
    grr_scheme: str
) -> Generator[RepositoryProtocol, None, None]:

    root_path = tmp_path_factory.mktemp("tabix_fsspec_proto")
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
    scheme = grr_scheme
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


@pytest.fixture(scope="module")
def tabix_fsspec_proto_utf8(
        tmp_path_factory: pytest.TempPathFactory) -> RepositoryProtocol:
    root_path = tmp_path_factory.mktemp("tabix_fsspec_proto_utf8")
    setup_directories(root_path, {
        "one": {
            GR_CONF_FILE_NAME: "",
        }
    })
    setup_tabix(
        root_path / "one" / "test.txt.gz",
        """
            #chrëm  pos_bëgin pos_ënd    ë1
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
        ##FORMAT=<ID=GT,Number=1,Type=String,Description="Gënééééééotype">
        ##contig=<ID=foo>
        ##contig=<ID=bar>
        #CHROM POS ID REF ALT QUAL FILTER INFO FORMAT m1
        foo    10  .  T   G     .    .      .    GT   0/1
        foo    13  .  T   G     .    .      .    GT   0/1
        bar    15  .  T   G     .    .      .    GT   1/1
        bar    16  .  T   G     .    .      .    GT   0/1
        """)
    return build_filesystem_test_protocol(root_path)


@pytest.mark.grr_tabix
def test_get_all_resources(tabix_fsspec_proto: RepositoryProtocol) -> None:
    proto = tabix_fsspec_proto
    resources = list(proto.get_all_resources())
    assert len(resources) == 5, resources


@pytest.mark.grr_tabix
def test_open_raw_file_read_three_a(
        tabix_fsspec_proto: RepositoryProtocol) -> None:
    # Given
    proto = tabix_fsspec_proto
    res = proto.get_resource("three")

    # When
    with proto.open_raw_file(res, "sub1/a.txt") as infile:
        content = infile.read()

    # Then
    assert content == "a"


@pytest.mark.grr_tabix
def test_open_raw_file_read_one_compressed(
        tabix_fsspec_proto: RepositoryProtocol) -> None:
    # Given
    proto = tabix_fsspec_proto
    res = proto.get_resource("one")

    # When
    with proto.open_raw_file(
            res, "test.txt.gz", compression="gzip") as infile:
        header = infile.readline()

    # Then
    assert header == "#chrom\tpos_begin\tpos_end\tc1\n"


@pytest.mark.grr_tabix
def test_open_raw_file_seek(tabix_fsspec_proto: RepositoryProtocol) -> None:
    # Given
    proto = tabix_fsspec_proto
    res = proto.get_resource("xxxxx-genome")

    # When
    with proto.open_raw_file(
            res, "chr.fa") as infile:

        infile.seek(7)
        sequence = infile.read(10)

    # Then
    assert sequence == "NNACCCAAAC"


@pytest.mark.grr_tabix
def test_open_tabix_file_contigs(
        tabix_fsspec_proto: RepositoryProtocol) -> None:
    # Given
    proto = tabix_fsspec_proto
    res = proto.get_resource("one")

    # When
    with proto.open_tabix_file(res, "test.txt.gz") as tabix:
        contigs = tabix.contigs

    # Then
    assert contigs == ["1", "2", "3"]


@pytest.mark.grr_tabix
def test_open_tabix_file_fetch_all(
        tabix_fsspec_proto: RepositoryProtocol) -> None:
    # Given
    proto = tabix_fsspec_proto
    res = proto.get_resource("one")

    # When
    lines = []
    with proto.open_tabix_file(res, "test.txt.gz") as tabix:

        for line in tabix.fetch():
            lines.append(line)

    # Then
    assert len(lines) == 5


@pytest.mark.grr_tabix
def test_open_tabix_file_fetch_region(
        tabix_fsspec_proto: RepositoryProtocol) -> None:
    # Given
    proto = tabix_fsspec_proto
    res = proto.get_resource("one")

    # When
    lines = []
    with proto.open_tabix_file(res, "test.txt.gz") as tabix:

        for line in tabix.fetch("3"):
            lines.append(line)

    # Then
    assert lines == ["3\t1\t10\t3.0", "3\t11\t20\t3.5"]


@pytest.mark.grr_tabix
def test_open_vcf_file_contigs(
        tabix_fsspec_proto: RepositoryProtocol) -> None:
    # Given
    proto = tabix_fsspec_proto
    res = proto.get_resource("one")
    # When
    with proto.open_vcf_file(res, "in.vcf.gz") as vcf:
        contigs = list(vcf.header.contigs)

    # Then
    assert contigs == ["foo", "bar"]


@pytest.mark.grr_tabix
def test_open_vcf_file_fetch_all(
        tabix_fsspec_proto: RepositoryProtocol) -> None:
    # Given
    proto = tabix_fsspec_proto
    res = proto.get_resource("one")

    # When
    lines = []
    with proto.open_vcf_file(res, "in.vcf.gz") as vcf:

        for line in vcf.fetch():
            lines.append(line)

    # Then
    assert len(lines) == 4


@pytest.mark.grr_tabix
def test_open_vcf_file_fetch_region(
        tabix_fsspec_proto: RepositoryProtocol) -> None:
    # Given
    proto = tabix_fsspec_proto
    res = proto.get_resource("one")

    # When
    lines = []
    with proto.open_vcf_file(res, "in.vcf.gz") as vcf:

        for line in vcf.fetch("foo"):
            lines.append(line)

    # Then
    assert len(lines) == 2


@pytest.mark.grr_tabix
def test_open_utf8_tabix_file(
        tabix_fsspec_proto_utf8: RepositoryProtocol) -> None:
    proto = tabix_fsspec_proto_utf8
    res = proto.get_resource("one")

    with proto.open_tabix_file(res, "test.txt.gz") as tabix:
        print(tabix.contigs)

    with proto.open_tabix_file(res, "in.vcf.gz") as vcf:
        print(vcf.contigs)
