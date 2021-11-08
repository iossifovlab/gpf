import pytest
# import time
import logging

# from subprocess import Popen, PIPE
from threading import Thread, Condition
from functools import partial

from http.server import ThreadingHTTPServer
# from http.client import HTTPConnection
from RangeHTTPServer import RangeRequestHandler

logger = logging.getLogger(__name__)


class HTTPRepositoryServer(Thread):

    def __init__(self, http_port, directory):
        super(HTTPRepositoryServer, self).__init__()

        self.http_port = http_port
        self.directory = directory
        self.httpd = None
        self.server_address = None
        self.ready = Condition()

    def run(self):
        handler_class = partial(
            RangeRequestHandler, directory=self.directory)

        self.server_address = ("localhost", self.http_port)
        handler_class.protocol_version = "HTTP/1.0"

        with ThreadingHTTPServer(self.server_address, handler_class) as httpd:
            sa = httpd.socket.getsockname()
            serve_message = \
                "Serving HTTP on {host} port {port} " \
                "(http://{host}:{port}/) ..."

            logger.info(serve_message.format(host=sa[0], port=sa[1]))
            self.httpd = httpd
            with self.ready:
                self.ready.notify()

            self.httpd.serve_forever()


@pytest.fixture(scope="module")
def resources_http_server(fixture_dirname):
    http_port = 16500
    directory = fixture_dirname("genomic_resources")

    http_server = HTTPRepositoryServer(http_port, directory)
    http_server.start()
    with http_server.ready:
        http_server.ready.wait()

    logger.info(
        f"HTTP repository test server started: {http_server.server_address}")

    yield http_server

    http_server.httpd.shutdown()
    http_server.join()


@pytest.fixture
def genomic_resource_fixture_dir_repo(fixture_dirname):
    from dae.genomic_resources.dir_repository import GenomicResourceDirRepo
    dr = fixture_dirname("genomic_resources")
    return GenomicResourceDirRepo("genomic_resource_fixture_dir_repo", dr)


@pytest.fixture
def genomic_resource_fixture_http_repo(resources_http_server):
    http_port = resources_http_server.http_port

    from dae.genomic_resources.url_repository import GenomicResourceURLRepo
    url = f"http://localhost:{http_port}"
    return GenomicResourceURLRepo("genomic_resource_fixture_url_repo", url)


'''


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




class FakeRepository(GenomicResourcesRepo):

    def create_resource(self, resource_id, path):
        return GenomicResource(Box({"id": resource_id}), repo=self)


@pytest.fixture
def fake_repo():
    fake_repo = FakeRepository("fake_repo_id", "/repo/path")
    return fake_repo

'''
