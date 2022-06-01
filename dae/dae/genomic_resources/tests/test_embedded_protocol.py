# pylint: disable=redefined-outer-name,C0114,C0116,protected-access

import pytest

from dae.genomic_resources.repository import GR_CONF_FILE_NAME
from dae.genomic_resources.embedded_protocol import \
    build_embedded_protocol, \
    _scan_for_resources, \
    _scan_for_resource_files


@pytest.fixture
def repo_content():
    demo_gtf_content = "TP53\tchr3\t300\t200"
    return {
        "one": {
            GR_CONF_FILE_NAME: "",
            "data.txt": "alabala"
        },
        "sub": {
            "two": {
                GR_CONF_FILE_NAME: "",
            },
            "two(1.0)": {
                GR_CONF_FILE_NAME: "type: gene_models\nfile: genes.gtf",
                "genes.gtf": demo_gtf_content,
            },
        },
        "three(2.0)": {
            GR_CONF_FILE_NAME: "",
            "sub1": {
                "a.txt": "a"
            },
            "sub2": {
                "b.txt": "b"
            }
        }
    }


def test_scan_content_for_resources(repo_content):
    result = list(_scan_for_resources(repo_content, []))

    assert len(result) == 4


def test_scan_for_resource_one_files(repo_content):
    # Given
    result = list(_scan_for_resources(repo_content, []))

    # When
    resource_id, version, content = result[0]
    assert resource_id == "one"
    assert version == (0, )

    resource_files = sorted(list(_scan_for_resource_files(content, [])))

    # Then
    assert len(resource_files) == 2

    assert resource_files[0] == ("data.txt", "alabala")
    assert resource_files[1] == (GR_CONF_FILE_NAME, "")


def test_scan_for_resource_two_0_files(repo_content):

    # Given
    result = list(_scan_for_resources(repo_content, []))

    # When
    resource_id, version, content = result[1]
    assert resource_id == "sub/two"
    assert version == (0, )

    resource_files = sorted(list(_scan_for_resource_files(content, [])))

    # Then
    assert len(resource_files) == 1

    assert resource_files[0] == (GR_CONF_FILE_NAME, "")


def test_scan_for_resource_two_1_files(repo_content):

    # Given
    result = list(_scan_for_resources(repo_content, []))

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


def test_scan_for_resource_three_files(repo_content):

    # Given
    result = list(_scan_for_resources(repo_content, []))

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


@pytest.fixture
def emb_proto(repo_content):
    proto = build_embedded_protocol("src", content=repo_content)
    return proto


def test_scan_path_for_resources(emb_proto):
    result = list(emb_proto._scan_path_for_resources([]))

    assert len(result) == 4
    res_id, res_version, res_path = result[0]
    assert res_id == "one"
    assert res_version == (0,)
    assert res_path == "one"

    result_files = sorted(list(
        emb_proto._scan_resource_for_files(res_path, [])))

    assert len(result_files) == 2
    assert result_files[0] == \
        ("data.txt", "memory:///test-repo/one/data.txt")
    assert result_files[1] == \
        (
            "genomic_resource.yaml",
            "memory:///test-repo/one/genomic_resource.yaml")

    res_id, res_version, res_path = result[3]
    assert res_id == "three"
    assert res_version == (2, 0)
    assert res_path == "three(2.0)"

    result_files = sorted(list(
        emb_proto._scan_resource_for_files(res_path, [])))

    assert len(result_files) == 3
    print(result_files)


def test_embedded_proto_simple(emb_proto):
    assert len(list(emb_proto.get_all_resources())) == 4


def test_get_resource(emb_proto):

    res = emb_proto.get_resource("sub/two")
    assert res.resource_id == "sub/two"
    assert res.version == (1, 0)


def test_load_manifest(emb_proto):

    res = emb_proto.get_resource("sub/two")
    manifest = emb_proto.load_manifest(res)

    entry = manifest["genes.gtf"]
    assert entry.name == "genes.gtf"
    assert entry.size == 17
    # assert entry.time == "2021-11-20T00:00:56+00:00"
    assert entry.md5 == "d9636a8dca9e5626851471d1c0ea92b1"


def test_get_manifest(emb_proto):

    res = emb_proto.get_resource("sub/two")
    manifest = emb_proto.get_manifest(res)

    entry = manifest["genes.gtf"]
    assert entry.name == "genes.gtf"
    assert entry.size == 17
    # assert entry.time == "2021-11-20T00:00:56+00:00"
    assert entry.md5 == "d9636a8dca9e5626851471d1c0ea92b1"
