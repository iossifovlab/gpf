# pylint: disable=W0621,C0114,C0116,W0212,W0613

import logging
import requests


logger = logging.getLogger(__name__)


def test_simple_experiment(fixtures_http_server):
    url = fixtures_http_server
    print(100 * "=")
    print(url)
    print(100 * "=")

    response = requests.get(f"{url}/.CONTENTS")
    assert response.status_code == 200
    logger.info("response: %s", response)
    logger.info("shutting down range http server...")

    logger.info("[DONE] shutting down range http server...")

