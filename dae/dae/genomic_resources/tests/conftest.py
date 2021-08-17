import pytest
import time
from dae.configuration.gpf_config_parser import FrozenBox
from subprocess import Popen, PIPE
from http.client import HTTPConnection


@pytest.fixture
def test_grdb_config(fixture_dirname, temp_dirname_grdb):
    test_grr_location = fixture_dirname("genomic_scores")
    return FrozenBox({
        "cache_location": temp_dirname_grdb,
        "genomic_resource_repositories": [
            {"id": "test_grr", "url": f"file://{test_grr_location}"}
        ]
    })


@pytest.fixture
def test_grdb_http_config(fixture_dirname, temp_dirname_grdb, http_port):
    return FrozenBox({
        "cache_location": temp_dirname_grdb,
        "genomic_resource_repositories": [
            {"id": "test_grr", "url": f"http://localhost:{http_port}"}
        ]
    })


@pytest.fixture(scope="session")
def http_port():
    return "16200"


@pytest.fixture(scope="module")
def resources_http_server(fixture_dirname, http_port):
    server = Popen(
        [
            "python",
            "-m", "RangeHTTPServer",
            http_port,
            "--bind", "localhost",
            "--directory", fixture_dirname("genomic_scores"),
        ],
        stdout=PIPE,
        encoding="utf-8",
        universal_newlines=True
    )
    retries = 5
    success = False
    while retries > 0:
        try:
            conn = HTTPConnection(f"localhost:{http_port}")
            conn.request("HEAD", "/")
            response = conn.getresponse()
            if response is not None:
                success = True
                yield server
                break
        except ConnectionRefusedError:
            time.sleep(0.5)
            retries -= 1

    if not success:
        raise RuntimeError("Failed to start local HTTP server")

    server.terminate()
    server.wait()
