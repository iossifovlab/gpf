import logging
import os

from threading import Thread, Condition
from functools import partial

from http.server import ThreadingHTTPServer

import pytest

from RangeHTTPServer import RangeRequestHandler  # type: ignore

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
def http_server(request):

    def builder(dirname):
        http_port = 16510

        http_server = HTTPRepositoryServer(http_port, dirname)
        http_server.start()
        with http_server.ready:
            http_server.ready.wait()

        logger.info(
            f"HTTP repository test server started: "
            f"{http_server.server_address}")

        def fin():
            http_server.httpd.shutdown()
            http_server.join()

        request.addfinalizer(fin)

        return http_server

    return builder


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


@pytest.fixture
def genomic_resource_fixture_s3_repo(genomic_resource_fixture_dir_repo, s3):
    src_dir = genomic_resource_fixture_dir_repo.directory
    s3_path = 's3://test-bucket'
    for root, _, files in os.walk(src_dir):
        for fn in files:
            root_rel = os.path.relpath(root, src_dir)
            if root_rel == '.':
                root_rel = ''
            s3.put(os.path.join(root, fn), os.path.join(s3_path, root_rel, fn))

    from dae.genomic_resources.url_repository import GenomicResourceURLRepo
    repo = GenomicResourceURLRepo("genomic_resource_fixture_url_repo", s3_path)
    repo.filesystem = s3
    return repo
