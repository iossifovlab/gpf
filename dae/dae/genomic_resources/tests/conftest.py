# pylint: disable=redefined-outer-name,C0114,C0115,C0116,protected-access

import logging
import os
import glob

from threading import Thread, Condition
from functools import partial

from http.server import ThreadingHTTPServer

import pytest  # type: ignore
import pysam

from RangeHTTPServer import RangeRequestHandler  # type: ignore

from dae.genomic_resources.repository import \
    GR_CONF_FILE_NAME, \
    GenomicResourceProtocolRepo
from dae.genomic_resources.fsspec_protocol import \
    build_fsspec_protocol
from dae.genomic_resources.testing import \
    build_testing_protocol, tabix_to_resource
from dae.genomic_resources.test_tools import convert_to_tab_separated


logger = logging.getLogger(__name__)


class HTTPRepositoryServer(Thread):

    def __init__(self, http_port, directory):
        super().__init__()

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
            saddr = httpd.socket.getsockname()
            logger.info(
                "Serving HTTP on (http://%s:%s/) ...", saddr[0], saddr[1])
            self.httpd = httpd
            with self.ready:
                self.ready.notify()

            self.httpd.serve_forever()


@pytest.fixture
def http_server(request):

    def builder(dirname):
        http_port = 16510

        http_server = HTTPRepositoryServer(http_port, dirname)
        http_server.start()
        with http_server.ready:
            http_server.ready.wait()

        logger.info(
            "HTTP repository test server started: %s",
            http_server.server_address)

        def fin():
            http_server.httpd.socket.close()
            http_server.httpd.shutdown()
            http_server.join()

        request.addfinalizer(fin)

        return http_server

    return builder


# @contextlib.contextmanager
# def serve():
#     port = 16510
#     server_address = ("", port)
#     httpd = HTTPServer(server_address, HTTPTestHandler)
#     th = threading.Thread(target=httpd.serve_forever)
#     th.daemon = True
#     th.start()
#     try:
#         yield "http://localhost:%i" % port
#     finally:
#         httpd.socket.close()
#         httpd.shutdown()
#         th.join()


# @pytest.fixture(scope="module")
# def server():
#     with serve() as s:
#         yield s


@pytest.fixture(scope="module")
def resources_http_server(fixture_dirname):
    http_port = 16500
    directory = fixture_dirname("genomic_resources")

    http_server = HTTPRepositoryServer(http_port, directory)
    http_server.start()
    with http_server.ready:
        http_server.ready.wait()

    logger.info(
        "HTTP repository test server started: %s", http_server.server_address)

    yield http_server

    http_server.httpd.shutdown()
    http_server.join()


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


@pytest.fixture
def proto_builder(
        request, tmp_path_factory,
        s3_base,  # pylint: disable=unused-argument
        http_server):

    def builder(src_proto, scheme="file", proto_id="testing"):

        def fin():
            for fname in glob.glob("*.tbi"):
                os.remove(fname)

        request.addfinalizer(fin)

        if scheme == "memory":
            tmp_dir = tmp_path_factory.mktemp(
                basename="file", numbered=True)
            proto = build_fsspec_protocol(proto_id, f"memory://{tmp_dir}")
            for res in src_proto.get_all_resources():
                proto.copy_resource(res)
            return proto

        if scheme == "file":

            tmp_dir = tmp_path_factory.mktemp(
                basename="file", numbered=True)
            proto = build_fsspec_protocol(proto_id, f"file://{tmp_dir}")
            for res in src_proto.get_all_resources():
                proto.copy_resource(res)
            return proto

        if scheme == "s3":
            # pylint: disable=import-outside-toplevel
            from botocore.session import Session  # type: ignore
            endpoint_url = "http://127.0.0.1:5555/"
            # NB: we use the sync botocore client for setup
            session = Session()
            client = session.create_client("s3", endpoint_url=endpoint_url)
            client.create_bucket(Bucket="test-bucket", ACL="public-read")

            tmp_dir = tmp_path_factory.mktemp(
                basename="s3", numbered=True)

            proto = build_fsspec_protocol(
                proto_id, f"s3://test-bucket{tmp_dir}",
                endpoint_url=endpoint_url)

            for res in src_proto.get_all_resources():
                proto.copy_resource(res)

            proto.filesystem.invalidate_cache()
            return proto

        if scheme == "http":
            tmp_dir = tmp_path_factory.mktemp(
                basename="http", numbered=True)

            proto = build_fsspec_protocol(
                f"{proto_id}_dir", f"file://{tmp_dir}")
            for res in src_proto.get_all_resources():
                proto.copy_resource(res)
            proto.build_content_file()

            http_server(str(tmp_dir))
            proto = build_fsspec_protocol(proto_id, "http://127.0.0.1:16510")

            proto.filesystem.invalidate_cache()
            return proto

        raise ValueError(f"unsupported scheme: {scheme}")

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
