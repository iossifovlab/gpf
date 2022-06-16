# pylint: disable=redefined-outer-name,C0114,C0116,protected-access

import textwrap

import pytest

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


@pytest.mark.parametrize("use_dvc,expected", [
    (True, "aaaa"),
    (False, "d861877da56b8b4ceb35c8cbfdf65bb4"),
])
def test_compute_md5_a_use_dvc(proto_fixture, use_dvc, expected):

    res = proto_fixture.get_resource("one")
    md5 = proto_fixture.compute_md5_sum(res, "sub/a.big", use_dvc=use_dvc)
    assert md5 == expected


@pytest.mark.parametrize("use_dvc,expected", [
    (True, "bbbb"),
    (False, "d861877da56b8b4ceb35c8cbfdf65bb4"),
])
def test_compute_md5_b_use_dvc(proto_fixture, use_dvc, expected):

    res = proto_fixture.get_resource("one")
    md5 = proto_fixture.compute_md5_sum(res, "b.big", use_dvc=use_dvc)
    assert md5 == expected


@pytest.mark.parametrize("use_dvc,filename,expected", [
    (True, "sub/a.big", ("aaaa", 3_000_000_000)),
    (False, "sub/a.big", ("d861877da56b8b4ceb35c8cbfdf65bb4", 3)),
    (True, "b.big", ("bbbb", 3_000_000_000)),
    (False, "b.big", ("d861877da56b8b4ceb35c8cbfdf65bb4", 3)),
])
def test_build_resource_file_state_use_dvc(
        proto_fixture, use_dvc, filename, expected):

    res = proto_fixture.get_resource("one")
    state = proto_fixture.build_resource_file_state(
        res, filename, use_dvc=use_dvc)
    md5, size = expected

    assert state.md5 == md5
    assert state.size == size


@pytest.mark.parametrize("use_dvc,filename,expected", [
    (True, "sub/a.big", ("aaaa", 3_000_000_000)),
    (False, "sub/a.big", ("d861877da56b8b4ceb35c8cbfdf65bb4", 3)),
    (True, "b.big", ("bbbb", 3_000_000_000)),
    (False, "b.big", ("d861877da56b8b4ceb35c8cbfdf65bb4", 3)),
])
def test_build_build_manifest_use_dvc(
        proto_fixture, use_dvc, filename, expected):

    res = proto_fixture.get_resource("one")
    manifest = proto_fixture.build_manifest(res, use_dvc=use_dvc)
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
    proto_fixture.save_manifest(res, proto_fixture.build_manifest(res))

    with proto_fixture.open_raw_file(res, filename, "wt") as outfile:
        outfile.write("bigger")

    manifest = proto_fixture.update_manifest(res, use_dvc=use_dvc)
    proto_fixture.save_manifest(res, manifest)

    manifest = proto_fixture.load_manifest(res)

    md5, size = expected
    entry = manifest[filename]

    assert entry.md5 == md5
    assert entry.size == size
