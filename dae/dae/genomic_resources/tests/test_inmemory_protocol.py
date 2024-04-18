# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pathlib
from typing import Any

from dae.genomic_resources.fsspec_protocol import (
    _scan_for_resource_files,
    _scan_for_resources,
)
from dae.genomic_resources.repository import GR_CONF_FILE_NAME
from dae.genomic_resources.testing import build_inmemory_test_protocol


def test_scan_content_for_resources(content_fixture: dict[str, Any]) -> None:
    result = list(_scan_for_resources(content_fixture, []))

    assert len(result) == 5


def test_scan_for_resource_one_files(
        content_fixture: dict[str, Any], alabala_gz: bytes) -> None:
    # Given
    result = list(_scan_for_resources(content_fixture, []))

    # When
    resource_id, version, content = result[0]
    assert resource_id == "one"
    assert version == (0, )

    resource_files = sorted(list(_scan_for_resource_files(content, [])))

    # Then
    assert len(resource_files) == 3

    assert resource_files[0] == ("data.txt", "alabala")
    assert resource_files[1] == ("data.txt.gz", alabala_gz)
    assert resource_files[2] == (GR_CONF_FILE_NAME, "")


def test_scan_for_resource_two_0_files(
        content_fixture: dict[str, Any]) -> None:

    # Given
    result = list(_scan_for_resources(content_fixture, []))

    # When
    resource_id, version, content = result[1]
    assert resource_id == "sub/two"
    assert version == (0, )

    resource_files = sorted(list(_scan_for_resource_files(content, [])))

    # Then
    assert len(resource_files) == 1

    assert resource_files[0] == (GR_CONF_FILE_NAME, "")


def test_scan_for_resource_two_1_files(
        content_fixture: dict[str, Any]) -> None:

    # Given
    result = list(_scan_for_resources(content_fixture, []))

    # When
    resource_id, version, content = result[2]
    assert resource_id == "sub/two"
    assert version == (1, 0)

    resource_files = sorted(list(_scan_for_resource_files(content, [])))

    # Then
    assert len(resource_files) == 2

    assert resource_files[0] == ("genes.gtf", "TP53\tchr3\t300\t200")
    assert resource_files[1] == \
        (GR_CONF_FILE_NAME, "type: gene_models\nfile: genes.gtf")


def test_scan_for_resource_three_files(
        content_fixture: dict[str, Any]) -> None:

    # Given
    result = list(_scan_for_resources(content_fixture, []))

    # When
    resource_id, version, content = result[3]
    assert resource_id == "three"
    assert version == (2, 0)

    resource_files = sorted(list(_scan_for_resource_files(content, [])))

    # Then
    assert len(resource_files) == 3

    assert resource_files[0] == (GR_CONF_FILE_NAME, "")
    assert resource_files[1] == ("sub1/a.txt", "a")
    assert resource_files[2] == ("sub2/b.txt", "b")


def test_scan_path_for_resources(
        content_fixture: dict[str, Any], tmp_path: pathlib.Path) -> None:
    proto = build_inmemory_test_protocol(content_fixture)
    result = list(proto._scan_path_for_resources([]))

    assert len(result) == 5
    res_id, res_version, res_path = result[0]
    assert res_id == "one"
    assert res_version == (0,)
    assert res_path == "one"

    result_files = sorted(list(
        proto._scan_resource_for_files(res_path, [])))

    assert len(result_files) == 3

    assert result_files[0][0] == "data.txt"
    assert result_files[0][1].endswith("/one/data.txt")

    assert result_files[1][0] == "data.txt.gz"
    assert result_files[1][1].endswith("/one/data.txt.gz")

    assert result_files[2][0] == "genomic_resource.yaml"
    assert result_files[2][1].endswith("/one/genomic_resource.yaml")

    res_id, res_version, res_path = result[3]
    assert res_id == "three"
    assert res_version == (2, 0)
    assert res_path == "three(2.0)"

    result_files = sorted(list(
        proto._scan_resource_for_files(res_path, [])))

    assert len(result_files) == 3
    print(result_files)


def test_inmemory_proto_simple(content_fixture: dict[str, Any]) -> None:
    proto = build_inmemory_test_protocol(content_fixture)
    assert len(list(proto.get_all_resources())) == 5


def test_get_resource(content_fixture: dict[str, Any]) -> None:
    proto = build_inmemory_test_protocol(content_fixture)
    res = proto.get_resource("sub/two")
    assert res.resource_id == "sub/two"
    assert res.version == (1, 0)


def test_load_manifest(content_fixture: dict[str, Any]) -> None:
    proto = build_inmemory_test_protocol(content_fixture)

    res = proto.get_resource("sub/two")
    manifest = proto.load_manifest(res)

    entry = manifest["genes.gtf"]
    assert entry.name == "genes.gtf"
    assert entry.size == 17
    # assert entry.time == "2021-11-20T00:00:56+00:00"
    assert entry.md5 == "d9636a8dca9e5626851471d1c0ea92b1"


def test_get_manifest(content_fixture: dict[str, Any]) -> None:
    proto = build_inmemory_test_protocol(content_fixture)

    res = proto.get_resource("sub/two")
    manifest = proto.get_manifest(res)

    entry = manifest["genes.gtf"]
    assert entry.name == "genes.gtf"
    assert entry.size == 17
    # assert entry.time == "2021-11-20T00:00:56+00:00"
    assert entry.md5 == "d9636a8dca9e5626851471d1c0ea92b1"
