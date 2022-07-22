# pylint: disable=W0621,C0114,C0116,W0212,W0613

import logging
import requests

from .conftest import HTTPRepositoryServer

logger = logging.getLogger(__name__)


def test_simple_experiment(fixture_dirname):
    directory = fixture_dirname("genomic_resources")

    server = HTTPRepositoryServer(16510, directory)
    server.start()

    with server.ready:
        server.ready.wait()
    logger.info("server started...")

    response = requests.get("http://localhost:16510/.CONTENTS")
    assert response.status_code == 200
    logger.info("response: %s", response)
    logger.info("shutting down range http server...")
    server.shutdown()
    logger.info("[DONE] shutting down range http server...")


