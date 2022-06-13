# pylint: disable=redefined-outer-name,C0114,C0116,protected-access

import gzip
import pytest

from dae.genomic_resources.repository import GR_CONF_FILE_NAME


@pytest.mark.parametrize("scheme", [
    "file",
    "memory",
    "s3",
    "http",
])
def test_all_repo_types(repo_builder, scheme):

    breh_gz = gzip.compress(b"breh")
    test_repo = repo_builder(
        content={
            "one": {
                GR_CONF_FILE_NAME: "opaa",
                "data.txt": "breh",
                "data.txt.gz": breh_gz
            }
        },
        scheme=scheme)

    res = test_repo.get_resource("one")
    files = sorted([fname for fname, _ in res.get_manifest().get_files()])
    assert files == ["data.txt", "data.txt.gz", GR_CONF_FILE_NAME]

    with res.open_raw_file("data.txt", "rt") as infile:
        content = infile.read(10)
        assert content == "breh"

    with res.open_raw_file("data.txt", "rb") as infile:
        content = infile.read(10)
        assert content == b"breh"

    with res.open_raw_file("data.txt.gz", "rb") as infile:
        content = infile.read()
        assert content == breh_gz

    with res.open_raw_file("data.txt.gz", "rt", compression=True) as infile:
        content = infile.read()
        assert content == "breh"
