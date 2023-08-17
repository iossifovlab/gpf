# pylint: disable=W0621,C0114,C0116,W0212,W0613
import os
import contextlib
import fcntl
import threading
import pathlib
from typing import Callable, Any, Generator, ContextManager, cast

import pytest
from pytest_mock import MockerFixture

from dae.genomic_resources.cli import _run_list_command
from dae.genomic_resources.repository import GR_CONF_FILE_NAME, \
    GenomicResourceProtocolRepo
from dae.genomic_resources.fsspec_protocol import FsspecReadWriteProtocol
from dae.genomic_resources.cached_repository import \
    GenomicResourceCachedRepo, CachingProtocol, \
    cache_resources
from dae.genomic_resources import build_genomic_resource_repository
from dae.genomic_resources.testing import build_inmemory_test_repository, \
    build_s3_test_server


def test_create_definition_with_cache(tmp_path: pathlib.Path) -> None:
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


CacheRepositoryBuilder = Callable[
    [dict[str, Any], str], ContextManager[GenomicResourceCachedRepo]]


@pytest.fixture
def cache_repository(
    tmp_path: pathlib.Path
) -> CacheRepositoryBuilder:

    @contextlib.contextmanager
    def builder(
        content: dict[str, Any], scheme: str = "file"
    ) -> Generator[GenomicResourceCachedRepo, None, None]:
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
def test_get_cached_resource(
        cache_repository: CacheRepositoryBuilder,
        scheme: str) -> None:

    with cache_repository(
            {"one": {"genomic_resource.yaml": ""}}, scheme) as cache_repo:

        res = cache_repo.get_resource("one")
        assert res.resource_id == "one"


@pytest.mark.parametrize("scheme", [
    "file",
    "s3",
])
def test_cached_repo_get_all_resources(
        cache_repository: CacheRepositoryBuilder, scheme: str) -> None:

    demo_gtf_content = "TP53\tchr3\t300\t200"
    with cache_repository({
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
            }}, scheme) as cache_repo:

        assert len(list(cache_repo.get_all_resources())) == 3

        resource = cache_repo.get_resource("sub/two")
        assert resource is not None


@pytest.mark.parametrize("scheme", [
    "file",
    "s3",
])
def test_cached_resource_after_access(
        cache_repository: CacheRepositoryBuilder, scheme: str) -> None:

    demo_gtf_content = "TP53\tchr3\t300\t200"
    with cache_repository({
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
            }}, scheme) as cache_repo:

        src_gr = cache_repo.child.get_resource("sub/two")
        cache_gr = cache_repo.get_resource("sub/two")

        assert src_gr.get_manifest() == cache_gr.get_manifest()
        assert len(list(cache_repo.get_all_resources())) == 3
        cache_proto = cache_gr.proto

        filesystem = cast(CachingProtocol, cache_proto)\
            .local_protocol.filesystem
        base_url = cast(CachingProtocol, cache_proto).local_protocol.url

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
def test_cache_all(
        cache_repository: CacheRepositoryBuilder, scheme: str) -> None:

    demo_gtf_content = "TP53\tchr3\t300\t200"
    with cache_repository({
            "one": {
                GR_CONF_FILE_NAME: "type: gene_models\nfilename: genes.gtf",
                "genes.gtf": demo_gtf_content
            },
            "sub": {
                "two-unstable(1.0)": {
                    GR_CONF_FILE_NAME:
                    "type: gene_models\nfilename: genes.gtf",
                    "genes.gtf": demo_gtf_content
                },
                "two(1.0)": {
                    GR_CONF_FILE_NAME:
                    "type: gene_models\nfilename: genes.gtf",
                    "genes.gtf": demo_gtf_content,
                }
            }}, scheme) as cache_repo:

        cache_resources(cache_repo, None, workers=1)

        resource = cache_repo.get_resource("one")
        cache_proto = resource.proto
        filesystem = cast(CachingProtocol, cache_proto)\
            .local_protocol.filesystem
        base_url = cast(CachingProtocol, cache_proto).local_protocol.url

        # import pdb; pdb.set_trace()

        assert filesystem.exists(
            os.path.join(base_url, "one", "genes.gtf"))
        assert filesystem.exists(
            os.path.join(base_url, "sub/two-unstable(1.0)", "genes.gtf"))
        assert filesystem.exists(
            os.path.join(base_url, "sub/two(1.0)", "genes.gtf"))


@pytest.mark.parametrize("scheme", [
    "file",
    "s3",
])
def test_cached_repository_resource_update_delete(
        cache_repository: CacheRepositoryBuilder, scheme: str) -> None:

    with cache_repository({
            "one": {
                GR_CONF_FILE_NAME: "",
                "data.txt": "alabala",
                "alabala.txt": "alabala",
            }}, scheme) as cache_repo:

        src_repo = cast(GenomicResourceProtocolRepo, cache_repo.child)

        gr1 = src_repo.get_resource("one")

        gr2 = cache_repo.get_resource("one")

        assert gr1.get_manifest() == gr2.get_manifest()

        with gr2.open_raw_file("alabala.txt") as infile:
            content = infile.read()
            assert content == "alabala"

        cast(FsspecReadWriteProtocol, src_repo.proto)\
            .delete_resource_file(gr1, "alabala.txt")

        manifest = cast(FsspecReadWriteProtocol, src_repo.proto)\
            .build_manifest(gr1)
        cast(FsspecReadWriteProtocol, src_repo.proto)\
            .save_manifest(gr1, manifest)

        gr2 = cache_repo.get_resource("one")

        assert not gr2.file_exists("alabala.txt")


@pytest.mark.parametrize("scheme", [
    "file",
    "s3",
])
def test_cached_repository_file_level_cache(
        cache_repository: CacheRepositoryBuilder, scheme: str) -> None:

    with cache_repository({
            "one": {
                GR_CONF_FILE_NAME: "config",
                "data.txt": "data",
                "alabala.txt": "alabala",
            }}, scheme) as cache_repo:

        resource = cache_repo.get_resource("one")
        assert resource is not None

        cache_proto = cache_repo.get_resource("one").proto
        filesystem = cast(CachingProtocol, cache_proto)\
            .local_protocol.filesystem
        base_url = cast(CachingProtocol, cache_proto)\
            .local_protocol.url

        assert not filesystem.exists(
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


def test_filesystem_caching_lock_implementation(
        mocker: MockerFixture,
        cache_repository: CacheRepositoryBuilder) -> None:
    with cache_repository({
            "one": {
                GR_CONF_FILE_NAME: "config",
                "data.txt": "data",
            }}, "file") as cache_repo:

        resource = cache_repo.get_resource("one")
        assert resource is not None

        obtain_lock_spy = mocker.spy(
            FsspecReadWriteProtocol, "obtain_resource_file_lock"
        )
        flock_spy = mocker.spy(fcntl, "flock")

        with resource.open_raw_file("data.txt"):
            cache_proto = cast(CachingProtocol, resource.proto)
            lockfile_path = cache_proto.local_protocol\
                ._get_resource_file_lockfile_path(resource, "data.txt")
            assert os.path.exists(lockfile_path)
            obtain_lock_spy.assert_called_once()
            flock_spy.assert_called_once()
            assert flock_spy.call_args[0][0].name == lockfile_path
            assert flock_spy.call_args[0][1] == fcntl.LOCK_EX


@pytest.mark.parametrize("scheme", [
    "file",
    # "s3",
])
def test_cached_repository_locks_file_when_caching(
        cache_repository: CacheRepositoryBuilder, scheme: str) -> None:
    with cache_repository({
            "one": {
                GR_CONF_FILE_NAME: "config",
                "data.txt": "data",
            }}, scheme) as cache_repo:

        resource = cache_repo.get_resource("one")
        assert resource is not None

        finished = threading.Barrier(2)
        resource_locked = threading.Barrier(2)

        orig = cast(CachingProtocol, resource.proto)\
            .local_protocol.update_resource_file

        times_called = 0

        def blocking_wrapper(*args: Any) -> None:
            nonlocal times_called
            orig(*args)
            times_called += 1
            resource_locked.wait()
            finished.wait()

        cast(CachingProtocol, resource.proto) \
            .local_protocol\
            .update_resource_file = blocking_wrapper  # type: ignore

        x = threading.Thread(target=resource.open_raw_file,
                             args=("data.txt",))
        y = threading.Thread(target=resource.open_raw_file,
                             args=("data.txt",))
        y.start()
        x.start()

        for i in (1, 2):
            resource_locked.wait()
            assert times_called == i
            # make sure the next thread calls blocking_wrapper only
            # AFTER the assertion for times_called has happened
            finished.wait()

        x.join()
        y.join()


@pytest.mark.parametrize("scheme", [
    "file",
    "s3",
])
def test_get_resource_cached_files(
        cache_repository: CacheRepositoryBuilder, scheme: str) -> None:
    with cache_repository({
            "one": {
                GR_CONF_FILE_NAME: "",
                "data1.txt": "alabala",
                "data2.txt": "alabala",
                "data3.txt": "alabala"
            }}, scheme) as cache_repo:
        cache_gr = cache_repo.get_resource("one")

        cache_proto = cache_gr.proto

        filesystem = cast(CachingProtocol, cache_proto)\
            .local_protocol.filesystem
        base_url = cast(CachingProtocol, cache_proto)\
            .local_protocol.url

        assert not filesystem.exists(
            os.path.join(base_url, "one", "data1.txt"))
        assert cache_repo.get_resource_cached_files("one") == set()

        with cache_gr.open_raw_file("data1.txt") as infile:
            content = infile.read()
            assert content == "alabala"

        assert filesystem.exists(
            os.path.join(base_url, "one", "data1.txt"))
        assert cache_repo.get_resource_cached_files("one") == {"data1.txt"}

        with cache_gr.open_raw_file("data2.txt") as infile:
            content = infile.read()
            assert content == "alabala"

        assert filesystem.exists(
            os.path.join(base_url, "one", "data2.txt"))
        assert cache_repo.get_resource_cached_files("one") == {
            "data1.txt", "data2.txt"
        }


def test_cached_repo_list_cli(
        cache_repository: CacheRepositoryBuilder,
        capsys: pytest.CaptureFixture) -> None:
    with cache_repository({
            "one": {
                GR_CONF_FILE_NAME: "",
                "genomic_resource.yaml": "",
                "data1.txt": "alabala",
                "data2.txt": "alabala"}}, "file") as cache_repo:
        cache_repo._repo_id = "test_grr"

        res = cache_repo.get_resource("one")
        assert res.resource_id == "one"

        with res.open_raw_file("data1.txt") as infile:
            content = infile.read()
            assert content == "alabala"

        _run_list_command(cache_repo, [])  # type: ignore
        out, err = capsys.readouterr()
        print(out)
        assert err == ""
        assert out == \
            "Basic                0        1/ 3 14.0 B       test_grr one\n"


def test_cached_repo_nested_list_cli(
        cache_repository: CacheRepositoryBuilder,
        capsys: pytest.CaptureFixture) -> None:
    with cache_repository({
            "one": {
                GR_CONF_FILE_NAME: "",
                "data.txt": "alabala"
            },
            "sub": {
                "two": {
                    GR_CONF_FILE_NAME: "type: gene_models\nfile: genes.gtf",
                    "data2.txt": "alabala2"
                }
            }}, "file") as cache_repo:
        cache_repo._repo_id = "test_grr"

        res = cache_repo.get_resource("sub/two")
        assert res.resource_id == "sub/two"

        with res.open_raw_file("data2.txt") as infile:
            content = infile.read()
            assert content == "alabala2"

        res = cache_repo.get_resource("one")
        assert res.resource_id == "one"

        with res.open_raw_file("data.txt") as infile:
            content = infile.read()
            assert content == "alabala"

        _run_list_command(cache_repo, [])  # type: ignore
        out, err = capsys.readouterr()
        print(out)
        assert err == ""
        assert out == \
            "Basic                0        1/ 2 7.0 B        test_grr one\n" \
            "gene_models          0        1/ 2 41.0 B       test_grr " \
            "sub/two\n"
