# pylint: disable=W0621,C0114,C0116,C0415,W0212,W0613

import gzip
import logging
from collections.abc import Generator
from typing import Any

import pytest

from dae.genomic_resources.fsspec_protocol import FsspecRepositoryProtocol
from dae.genomic_resources.repository import GR_CONF_FILE_NAME
from dae.genomic_resources.testing import (
    build_filesystem_test_protocol,
    build_http_test_protocol,
    build_inmemory_test_protocol,
    convert_to_tab_separated,
    copy_proto_genomic_resources,
    s3_test_protocol,
    setup_directories,
)

logger = logging.getLogger(__name__)


@pytest.fixture(scope="session")
def alabala_gz() -> bytes:
    return gzip.compress(b"alabala")


@pytest.fixture()
def content_fixture(alabala_gz: bytes) -> dict[str, Any]:
    demo_gtf_content = "TP53\tchr3\t300\t200"

    return {
        "one": {
            GR_CONF_FILE_NAME: "",
            "data.txt": "alabala",
            "data.txt.gz": alabala_gz,
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
                "a.txt": "a",
            },
            "sub2": {
                "b.txt": "b",
            },
        },
        "xxxxx-genome": {
            "genomic_resource.yaml": "type: genome\nfilename: chr.fa",
            "chr.fa": convert_to_tab_separated(
                """
                    >xxxxx
                    NNACCCAAAC
                    GGGCCTTCCN
                    NNNA
                """),
            "chr.fa.fai": "xxxxx\t24\t7\t10\t11\n",
        },
    }


@pytest.fixture()
def fsspec_proto(
    request: pytest.FixtureRequest,
    content_fixture: dict[str, Any],
    tmp_path_factory: pytest.TempPathFactory,
    grr_scheme: str,
) -> Generator[FsspecRepositoryProtocol, None, None]:

    root_path = tmp_path_factory.mktemp("rw_fsspec_proto")
    setup_directories(root_path, content_fixture)

    if grr_scheme == "file":
        yield build_filesystem_test_protocol(root_path)
        return

    if grr_scheme == "s3":
        proto = s3_test_protocol()
        copy_proto_genomic_resources(
            proto,
            build_filesystem_test_protocol(root_path))
        yield proto
        return

    if grr_scheme == "inmemory":
        yield build_inmemory_test_protocol(content=content_fixture)
        return

    if grr_scheme == "http":
        with build_http_test_protocol(root_path) as http_proto:
            yield http_proto
        return

    raise ValueError(f"unexpected protocol scheme: <{grr_scheme}>")
