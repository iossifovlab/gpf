# pylint: disable=W0621,C0114,C0116,W0212,W0613

import logging
import requests

from dae.genomic_resources.testing import \
    range_http_process_server_generator, s3_moto_server
from dae.genomic_resources.repository_factory import \
    build_genomic_resource_repository
from dae.genomic_resources.clinvar import ClinVarVcf

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


def test_process_server_simple(fixture_dirname):
    directory = fixture_dirname("genomic_resources")
    logger.info("serving directory %s", directory)
    gen = range_http_process_server_generator(directory)
    url = next(gen)
    logger.info("echo...")

    response = requests.get(f"{url}/.CONTENTS")
    assert response.status_code == 200
    logger.info("response: %s", response)
    logger.info("shutting down range http server...")

    repositories = {
        "id": "test_grr",
        "type": "url",
        "url": url,
    }

    repo = build_genomic_resource_repository(repositories)
    res = repo.get_resource("clinvar")
    assert res is not None

    clinvar = ClinVarVcf(res)
    assert clinvar is not None

    clinvar.open()
    assert clinvar.is_open()

    print(100 * "=")
    print(10 * "DONE  ")
    print(100 * "=")
    try:
        next(gen)
    except StopIteration:
        pass


def test_s3_threading_server():
    # pylint: disable=import-outside-toplevel
    with s3_moto_server() as s3_url:

        print(100 * "=")
        print("s3:", s3_url)
        print(100 * "=")

        from botocore.session import Session  # type: ignore

        # NB: we use the sync botocore client for setup
        session = Session()
        client = session.create_client("s3", endpoint_url=s3_url)
        client.create_bucket(Bucket="test-bucket", ACL="public-read")

        from s3fs.core import S3FileSystem  # type: ignore

        S3FileSystem.clear_instance_cache()
        s3 = S3FileSystem(anon=False, client_kwargs={"endpoint_url": s3_url})
        s3.invalidate_cache()

        assert s3.ls("test-bucket") is not None
