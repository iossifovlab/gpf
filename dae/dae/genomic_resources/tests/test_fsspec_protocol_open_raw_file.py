# pylint: disable=W0621,C0114,C0116,W0212,W0613

from dae.genomic_resources.repository import GR_CONF_FILE_NAME, \
    RepositoryProtocol


def test_open_raw_files(
        fsspec_proto: RepositoryProtocol,
        alabala_gz: bytes) -> None:
    res = fsspec_proto.get_resource("one")
    files = sorted([fname for fname, _ in res.get_manifest().get_files()])
    assert files == ["data.txt", "data.txt.gz", GR_CONF_FILE_NAME]

    with res.open_raw_file("data.txt", "rt") as infile:
        content = infile.read(10)
        assert content == "alabala"

    with res.open_raw_file("data.txt", "rb") as infile:
        content = infile.read(10)
        assert content == b"alabala"

    with res.open_raw_file("data.txt.gz", "rb") as infile:
        content = infile.read()
        assert content == alabala_gz

    with res.open_raw_file("data.txt.gz", "rt", compression=True) as infile:
        content = infile.read()
        assert content == "alabala"
