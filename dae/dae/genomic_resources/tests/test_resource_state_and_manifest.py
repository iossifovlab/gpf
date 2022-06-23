# pylint: disable=W0621,C0114,C0116,W0212,W0613

import textwrap

import pytest

from dae.genomic_resources.cli import collect_dvc_entries
from dae.genomic_resources.repository import GR_CONF_FILE_NAME
from dae.genomic_resources.testing import build_testing_protocol


@pytest.fixture
def proto_fixture(tmp_path):
    proto = build_testing_protocol(
        scheme="memory",
        root_path=str(tmp_path),
        content={
            "one": {
                GR_CONF_FILE_NAME: "",
                "data.txt": "alabala",
                "b.big": "big",
                "b.big.dvc": textwrap.dedent("""
                    outs:
                    - md5: bbbb
                      path: b.big
                      size: 3000000000
                """),
                "sub": {
                    "a.big": "big",
                    "a.big.dvc": textwrap.dedent("""
                        outs:
                        - md5: aaaa
                          path: a.big
                          size: 3000000000
                    """)
                }
            },
        })
    return proto


@pytest.mark.parametrize("use_dvc,filename,expected", [
    (True, "sub/a.big", ("aaaa", 3_000_000_000)),
    (False, "sub/a.big", ("d861877da56b8b4ceb35c8cbfdf65bb4", 3)),
    (True, "b.big", ("bbbb", 3_000_000_000)),
    (False, "b.big", ("d861877da56b8b4ceb35c8cbfdf65bb4", 3)),
])
def test_build_build_manifest_use_dvc(
        proto_fixture, use_dvc, filename, expected):

    res = proto_fixture.get_resource("one")
    prebuild_entries = {}
    if use_dvc:
        prebuild_entries = collect_dvc_entries(proto_fixture, res)

    manifest = proto_fixture.build_manifest(res, prebuild_entries)
    md5, size = expected
    entry = manifest[filename]

    assert entry.md5 == md5
    assert entry.size == size


@pytest.mark.parametrize("use_dvc,filename,expected", [
    (True, "sub/a.big", ("aaaa", 3_000_000_000)),
    (False, "sub/a.big", ("7de99d55a70b4e1215218f00d95a9720", 6)),
    (True, "b.big", ("bbbb", 3_000_000_000)),
    (False, "b.big", ("7de99d55a70b4e1215218f00d95a9720", 6)),
])
def test_build_update_manifest_use_dvc(
        proto_fixture, use_dvc, filename, expected):

    res = proto_fixture.get_resource("one")

    prebuild_entries = {}
    if use_dvc:
        prebuild_entries = collect_dvc_entries(proto_fixture, res)

    proto_fixture.save_manifest(
        res, proto_fixture.build_manifest(res, prebuild_entries))

    with proto_fixture.open_raw_file(res, filename, "wt") as outfile:
        outfile.write("bigger")

    manifest = proto_fixture.update_manifest(res, prebuild_entries)
    proto_fixture.save_manifest(res, manifest)

    manifest = proto_fixture.load_manifest(res)

    md5, size = expected
    entry = manifest[filename]

    assert entry.md5 == md5
    assert entry.size == size
