import pytest
import time
import logging

from subprocess import Popen, PIPE
from http.client import HTTPConnection

from box import Box

from dae.configuration.gpf_config_parser import FrozenBox
from dae.genomic_resources.repository import GenomicResourcesRepo
from dae.genomic_resources.resources import GenomicResource, \
    GenomicResourceGroup
from dae.genomic_resources.resource_db import GenomicResourceDB

logger = logging.getLogger(__name__)


@pytest.fixture
def genomic_group():
    g1 = GenomicResourceGroup("a", "url1")
    g2 = GenomicResourceGroup("a/b", "url2")

    g1.add_child(g2)

    g3 = GenomicResourceGroup("a/b/c", "url3")
    g2.add_child(g3)

    print(g1.resource_children())

    r = GenomicResource(Box({"id": "a/b/c/d"}), None)
    g3.add_child(r)

    return g1


@pytest.fixture
def root_group():
    g1 = GenomicResourceGroup("", "url1")
    g2 = GenomicResourceGroup("a", "url2")

    g1.add_child(g2)

    g3 = GenomicResourceGroup("a/b", "url3")
    g2.add_child(g3)

    print(g1.resource_children())

    r = GenomicResource(Box({"id": "a/b/c"}), None)
    g3.add_child(r)

    return g1


@pytest.fixture
def test_grdb_config(fixture_dirname, temp_dirname_grdb):
    test_grr_location = fixture_dirname("genomic_resources")
    return FrozenBox({
        "genomic_resource_repositories": [
            {"id": "test_grr", "url": f"file://{test_grr_location}"}
        ]
    })


@pytest.fixture
def test_cached_grdb_config(fixture_dirname, temp_dirname_grdb):
    test_grr_location = fixture_dirname("genomic_resources")
    return FrozenBox({
        "genomic_resource_repositories": [
            {
                "id": "test_grr",
                "url": f"file://{test_grr_location}",
                "cache": f"file://{temp_dirname_grdb}",
            }
        ]
    })


@pytest.fixture
def test_grdb(test_grdb_config):
    grdb = GenomicResourceDB(
        test_grdb_config["genomic_resource_repositories"])
    assert len(grdb.repositories) == 1

    return grdb


# @pytest.fixture(scope="session")
# def http_port():
#     return "16200"


@pytest.fixture
def test_grdb_http_config(temp_dirname_grdb, resources_http_server):
    http_port = resources_http_server.http_port

    return FrozenBox({
        "genomic_resource_repositories": [
            {"id": "test_grr", "url": f"http://localhost:{http_port}"}
        ]
    })


@pytest.fixture
def test_cached_grdb_http_config(temp_dirname_grdb, resources_http_server):
    http_port = resources_http_server.http_port

    return FrozenBox({
        "genomic_resource_repositories": [
            {
                "id": "test_grr",
                "url": f"http://localhost:{http_port}",
                "cache": f"file://{temp_dirname_grdb}",
            }
        ]
    })


@pytest.fixture
def test_http_grdb(test_grdb_http_config):
    grdb = GenomicResourceDB(
        test_grdb_http_config["genomic_resource_repositories"])
    assert len(grdb.repositories) == 1

    return grdb


@pytest.fixture(scope="session")
def resources_http_server(fixture_dirname):

    http_port = 16200
    retries = 5
    success = False

    while retries > 0:
        http_port += 1
        logger.info(f"trying to start testing http server at {http_port}")
        try:
            server = Popen(
                [
                    "python",
                    "-m", "RangeHTTPServer",
                    f"{http_port}",
                    "--bind", "localhost",
                    "--directory", fixture_dirname("genomic_resources"),
                ],
                stdout=PIPE,
                encoding="utf-8",
                universal_newlines=True
            )
        except Exception:
            pass

        try:
            conn = HTTPConnection(f"localhost:{http_port}")
            conn.request("HEAD", "/")
            response = conn.getresponse()
            if response is not None:
                success = True
                server.http_port = http_port
                yield server
                break
        except ConnectionRefusedError:
            time.sleep(0.5)
            retries -= 1
            http_port += 1

        except OSError:
            time.sleep(0.5)
            retries -= 1
            http_port += 1

    if not success:
        raise RuntimeError("Failed to start local HTTP server")

    server.terminate()
    server.wait()


class FakeRepository(GenomicResourcesRepo):

    def create_resource(self, resource_id, path):
        return GenomicResource(Box({"id": resource_id}), repo=self)


@pytest.fixture
def fake_repo():
    fake_repo = FakeRepository("fake_repo_id", "/repo/path")
    return fake_repo
