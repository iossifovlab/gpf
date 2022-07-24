# pylint: disable=W0621,C0114,C0116,C0415,W0212,W0613

import logging
import os
import glob

import pytest  # type: ignore
import pysam

from dae.genomic_resources.repository import \
    GR_CONF_FILE_NAME, \
    GenomicResourceProtocolRepo
from dae.genomic_resources.fsspec_protocol import \
    build_fsspec_protocol
from dae.genomic_resources.testing import \
    build_testing_protocol, \
    range_http_process_server_generator, \
    s3_moto_server, \
    tabix_to_resource
from dae.genomic_resources.test_tools import convert_to_tab_separated
from dae.genomic_resources import build_genomic_resource_repository

logger = logging.getLogger(__name__)


@pytest.fixture
def grr_http(fixtures_http_server):  # pylint: disable=unused-argument
    # resources_http_server):
    url = fixtures_http_server
    repositories = {
        "id": "test_grr",
        "type": "url",
        "url": url,
    }

    return build_genomic_resource_repository(repositories)


@pytest.fixture
def tabix_file(tmp_path_factory):

    def builder(content, **kwargs):
        content = convert_to_tab_separated(content)
        tmpfilename = tmp_path_factory.mktemp(
            basename="tabix", numbered=True) / "temp_tabix.txt"
        with open(tmpfilename, "wt", encoding="utf8") as outfile:
            outfile.write(content)
        tabix_filename = f"{tmpfilename}.gz"
        index_filename = f"{tabix_filename}.tbi"

        # pylint: disable=no-member
        pysam.tabix_compress(tmpfilename, tabix_filename)
        pysam.tabix_index(tabix_filename, **kwargs)

        return tabix_filename, index_filename

    return builder


@pytest.fixture
def embedded_proto(tmp_path):

    def builder(
            content=None,
            proto_id="test_embedded", path=tmp_path):

        proto = build_testing_protocol(
            scheme="memory",
            proto_id=proto_id,
            root_path=str(path),
            content=content)

        return proto
    return builder


@pytest.fixture(scope="session")
def s3_moto_fixture():
    with s3_moto_server() as s3_url:

        from botocore.session import Session  # type: ignore
        session = Session()
        client = session.create_client("s3", endpoint_url=s3_url)
        client.create_bucket(Bucket="test-bucket", ACL="public-read")

        yield s3_url


@pytest.fixture
def proto_builder(
        request, tmp_path_factory, s3_moto_fixture):
    # flake8: noqa
    def builder(src_proto, scheme="file", proto_id="testing"):

        http_server_gen = None
        proto = None

        if scheme == "memory":
            tmp_dir = tmp_path_factory.mktemp(
                basename="file", numbered=True)
            proto = build_fsspec_protocol(proto_id, f"memory://{tmp_dir}")
            for res in src_proto.get_all_resources():
                proto.copy_resource(res)

        if scheme == "file":

            tmp_dir = tmp_path_factory.mktemp(
                basename="file", numbered=True)
            proto = build_fsspec_protocol(proto_id, f"file://{tmp_dir}")
            for res in src_proto.get_all_resources():
                proto.copy_resource(res)

        if scheme == "s3":
            endpoint_url = s3_moto_fixture

            tmp_dir = tmp_path_factory.mktemp(
                basename="s3", numbered=True)

            proto = build_fsspec_protocol(
                proto_id, f"s3://test-bucket{tmp_dir}",
                endpoint_url=endpoint_url)

            for res in src_proto.get_all_resources():
                proto.copy_resource(res)

            proto.filesystem.invalidate_cache()

        if scheme == "http":
            tmp_dir = tmp_path_factory.mktemp(
                basename="http", numbered=True)

            http_server_gen = range_http_process_server_generator(str(tmp_dir))
            url = next(http_server_gen)

            proto = build_fsspec_protocol(
                f"{proto_id}_dir", f"file://{tmp_dir}")
            for res in src_proto.get_all_resources():
                proto.copy_resource(res)
            proto.build_content_file()

            proto = build_fsspec_protocol(proto_id, url)

            proto.filesystem.invalidate_cache()

        if proto is None:
            raise ValueError(f"unsupported scheme: {scheme}")

        def fin():
            for fname in glob.glob("*.tbi"):
                os.remove(fname)
            if http_server_gen is not None:
                try:
                    next(http_server_gen)
                except StopIteration:
                    pass

        request.addfinalizer(fin)
        return proto

    return builder


@pytest.fixture
def resource_builder(proto_builder, embedded_proto):

    def builder(content, scheme="file", repo_id="testing"):
        repo_content = {
            "t": content
        }
        src_proto = embedded_proto(
            content=repo_content,
            proto_id=repo_id)

        proto = proto_builder(
            src_proto, scheme=scheme, proto_id=repo_id,)

        repo = GenomicResourceProtocolRepo(proto)

        return repo.get_resource("t")

    return builder


@pytest.fixture
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


@pytest.fixture
def fsspec_proto(proto_builder, embedded_proto, content_fixture, tabix_file):

    def builder(
            scheme="file", proto_id="testing"):

        src_proto = embedded_proto(content_fixture)
        res = src_proto.get_resource("one")
        tabix_to_resource(
            tabix_file(
                """
                    #chrom  pos_begin  pos_end    c1
                    1      1          10         1.0
                    2      1          10         2.0
                    2      11         20         2.5
                    3      1          10         3.0
                    3      11         20         3.5
                """,
                seq_col=0, start_col=1, end_col=2),
            res,
            filename="test.txt.gz")

        proto = proto_builder(
            src_proto, scheme=scheme, proto_id=proto_id)

        return proto

    return builder


@pytest.fixture
def fsspec_repo(fsspec_proto):

    def builder(scheme, repo_id="testing"):
        proto = fsspec_proto(
            scheme, proto_id=repo_id)
        repo = GenomicResourceProtocolRepo(proto)
        return repo

    return builder


@pytest.fixture
def repo_builder(proto_builder, embedded_proto):

    def builder(content, scheme="file", repo_id="testing"):
        src_proto = embedded_proto(content=content)
        proto = proto_builder(src_proto, scheme=scheme, proto_id=repo_id)
        return GenomicResourceProtocolRepo(proto)

    return builder
