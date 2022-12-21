# pylint: disable=W0621,C0114,C0116,C0415,W0212,W0613

import logging

import pytest
# import pysam

from dae.genomic_resources.repository import \
    GR_CONF_FILE_NAME
from dae.genomic_resources.testing import \
    build_filesystem_test_protocol
from dae.genomic_resources.testing import convert_to_tab_separated, \
    setup_directories
from dae.genomic_resources.testing import \
    s3_test_protocol, \
    s3_process_test_server, \
    copy_proto_genomic_resources

logger = logging.getLogger(__name__)


@pytest.fixture(scope="session")
def content_fixture():
    demo_gtf_content = "TP53\tchr3\t300\t200"
    return {
        "one": {
            GR_CONF_FILE_NAME: "",
            "data.txt": "alabala"
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
                "a.txt": "a"
            },
            "sub2": {
                "b.txt": "b"
            }
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
            "chr.fa.fai": "xxxxx\t24\t7\t10\t11\n"
        }
    }


@pytest.fixture(scope="module")
def s3_server_fixture():
    with s3_process_test_server() as endpoint_url:
        yield endpoint_url


@pytest.fixture(params=["file", "s3"])
def rw_fsspec_proto(
        request, content_fixture, tmp_path_factory, s3_server_fixture):

    root_path = tmp_path_factory.mktemp("rw_fsspec_proto")
    setup_directories(root_path, content_fixture)

    scheme = request.param
    if scheme == "file":
        yield build_filesystem_test_protocol(root_path)
        return
    if scheme == "s3":
        proto = s3_test_protocol(s3_server_fixture)
        copy_proto_genomic_resources(
            proto,
            build_filesystem_test_protocol(root_path))
        yield proto
        return

    raise ValueError(f"unexpected protocol scheme: <{scheme}>")
