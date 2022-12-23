# pylint: disable=W0621,C0114,C0116,W0212,W0613
import os
import contextlib
import pytest

from dae.genomic_resources.repository import GR_CONF_FILE_NAME
from dae.genomic_resources.cached_repository import GenomicResourceCachedRepo
from dae.genomic_resources import build_genomic_resource_repository
from dae.genomic_resources.testing import build_inmemory_test_repository, \
    build_s3_test_server


def test_create_definition_with_cache(tmp_path):
    repo = build_genomic_resource_repository(
        {
            "cache_dir": str(tmp_path / "cache"),
            "id": "bla",
            "type": "embedded",
            "content": {
                "one": {"genomic_resource.yaml": ""}
            }
        })
    assert isinstance(repo, GenomicResourceCachedRepo)

    res = repo.get_resource("one")
    assert res.resource_id == "one"


@pytest.fixture
def cache_repository(tmp_path):

    @contextlib.contextmanager
    def builder(content, scheme="file"):
        remote_repo = build_inmemory_test_repository(content)

        if scheme == "s3":
            with build_s3_test_server() as (bucket_url, endpoint_url):
                cache_repo = GenomicResourceCachedRepo(
                    remote_repo,
                    f"{bucket_url}/cache_repo_testing.caching",
                    endpoint_url=endpoint_url)
                yield cache_repo
        elif scheme == "file":
            cache_repo = GenomicResourceCachedRepo(
                remote_repo,
                f"file://{tmp_path}/cache_repo_testing.caching")
            yield cache_repo
        else:
            raise ValueError(f"unexpected scheme <{scheme}>")

    return builder


@pytest.mark.parametrize("scheme", [
    "file",
    "s3",
])
def test_get_cached_resource(cache_repository, scheme):

    with cache_repository(
            content={"one": {"genomic_resource.yaml": ""}},
            scheme=scheme) as cache_repo:

        res = cache_repo.get_resource("one")
        assert res.resource_id == "one"


@pytest.mark.parametrize("scheme", [
    "file",
    "s3",
])
def test_cached_repo_get_all_resources(cache_repository, scheme):

    demo_gtf_content = "TP53\tchr3\t300\t200"
    with cache_repository(content={
            "one": {
                GR_CONF_FILE_NAME: "",
                "data.txt": "alabala"
            },
            "sub": {
                "two-unstable(1.0)": {
                    GR_CONF_FILE_NAME: "type: gene_models\nfile: genes.gtf",
                    "genes.txt": demo_gtf_content
                },
                "two(1.0)": {
                    GR_CONF_FILE_NAME: "type: gene_models\nfile: genes.gtf",
                    "genes.txt": demo_gtf_content,
                }
            }}, scheme=scheme) as cache_repo:

        assert len(list(cache_repo.get_all_resources())) == 3


@pytest.mark.parametrize("scheme", [
    "file",
    "s3",
])
def test_cached_resource_after_access(cache_repository, scheme):

    demo_gtf_content = "TP53\tchr3\t300\t200"
    with cache_repository(content={
            "one": {
                GR_CONF_FILE_NAME: "",
                "data.txt": "alabala"
            },
            "sub": {
                "two-unstable(1.0)": {
                    GR_CONF_FILE_NAME: "type: gene_models\nfile: genes.gtf",
                    "genes.txt": demo_gtf_content
                },
                "two(1.0)": {
                    GR_CONF_FILE_NAME: "type: gene_models\nfile: genes.gtf",
                    "genes.txt": demo_gtf_content,
                }
            }}, scheme=scheme) as cache_repo:

        src_gr = cache_repo.child.get_resource("sub/two")
        cache_gr = cache_repo.get_resource("sub/two")

        assert src_gr.get_manifest() == cache_gr.get_manifest()
        assert len(list(cache_repo.get_all_resources())) == 3
        cache_proto = cache_gr.proto

        filesystem = cache_proto.local_protocol.filesystem
        base_url = cache_proto.local_protocol.url

        assert not filesystem.exists(
            os.path.join(base_url, "one", "data.txt"))
        assert not filesystem.exists(
            os.path.join(base_url, "sub/two-unstable(1.0)", "genes.txt"))
        assert not filesystem.exists(
            os.path.join(base_url, "sub/two(1.0)", "genes.txt"))


@pytest.mark.parametrize("scheme", [
    "file",
    "s3",
])
def test_cache_all(cache_repository, scheme):

    demo_gtf_content = "TP53\tchr3\t300\t200"
    with cache_repository(content={
            "one": {
                GR_CONF_FILE_NAME: "",
                "data.txt": "alabala"
            },
            "sub": {
                "two-unstable(1.0)": {
                    GR_CONF_FILE_NAME: "type: gene_models\nfile: genes.gtf",
                    "genes.txt": demo_gtf_content
                },
                "two(1.0)": {
                    GR_CONF_FILE_NAME: "type: gene_models\nfile: genes.gtf",
                    "genes.txt": demo_gtf_content,
                }
            }}, scheme=scheme) as cache_repo:

        cache_repo.cache_resources()

        cache_proto = cache_repo.get_resource("one").proto
        filesystem = cache_proto.local_protocol.filesystem
        base_url = cache_proto.local_protocol.url

        assert filesystem.exists(
            os.path.join(base_url, "one", "data.txt"))
        assert filesystem.exists(
            os.path.join(base_url, "sub/two-unstable(1.0)", "genes.txt"))
        assert filesystem.exists(
            os.path.join(base_url, "sub/two(1.0)", "genes.txt"))


@pytest.mark.parametrize("scheme", [
    "file",
    "s3",
])
def test_cached_repository_resource_update_delete(cache_repository, scheme):

    with cache_repository(content={
            "one": {
                GR_CONF_FILE_NAME: "",
                "data.txt": "alabala",
                "alabala.txt": "alabala",
            }}, scheme=scheme) as cache_repo:
        src_repo = cache_repo.child

        gr1 = src_repo.get_resource("one")

        gr2 = cache_repo.get_resource("one")

        assert gr1.get_manifest() == gr2.get_manifest()

        with gr2.open_raw_file("alabala.txt") as infile:
            content = infile.read()
            assert content == "alabala"

        src_repo.proto.delete_resource_file(gr1, "alabala.txt")
        src_repo.proto.save_manifest(
            gr1,
            src_repo.proto.build_manifest(gr1))

        gr2 = cache_repo.get_resource("one")

        assert not gr2.file_exists("alabala.txt")


@pytest.mark.parametrize("scheme", [
    "file",
    "s3",
])
def test_cached_repository_file_level_cache(cache_repository, scheme):

    with cache_repository(content={
            "one": {
                GR_CONF_FILE_NAME: "config",
                "data.txt": "data",
                "alabala.txt": "alabala",
            }}, scheme=scheme) as cache_repo:

        resource = cache_repo.get_resource("one")
        assert resource is not None

        cache_proto = cache_repo.get_resource("one").proto
        filesystem = cache_proto.local_protocol.filesystem
        base_url = cache_proto.local_protocol.url

        assert filesystem.exists(
            os.path.join(base_url, "one", GR_CONF_FILE_NAME))
        assert not filesystem.exists(
            os.path.join(base_url, "one", "data.txt"))
        assert not filesystem.exists(
            os.path.join(base_url, "one", "alabala.txt"))

        with resource.open_raw_file("alabala.txt") as infile:
            content = infile.read()
            assert content == "alabala"

        assert not filesystem.exists(
            os.path.join(base_url, "one", "data.txt"))
        assert filesystem.exists(
            os.path.join(base_url, "one", "alabala.txt"))
