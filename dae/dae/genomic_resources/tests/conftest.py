# pylint: disable=redefined-outer-name,C0114,C0115,C0116,protected-access

import logging
import os
import tempfile
import shutil
import glob

from threading import Thread, Condition
from functools import partial

from http.server import ThreadingHTTPServer

import pytest  # type: ignore
import pysam

from RangeHTTPServer import RangeRequestHandler  # type: ignore

from dae.genomic_resources.repository import \
    GR_CONF_FILE_NAME
from dae.genomic_resources.fsspec_protocol import \
    build_fsspec_protocol
from dae.genomic_resources.embedded_protocol import \
    build_embedded_protocol
from dae.genomic_resources.dir_repository import GenomicResourceDirRepo
from dae.genomic_resources.url_repository import GenomicResourceURLRepo
from dae.genomic_resources.test_tools import convert_to_tab_separated


logger = logging.getLogger(__name__)


def relative_to_this_test_folder(path):
    return os.path.join(os.path.dirname(os.path.realpath(__file__)), path)


@pytest.fixture(scope="session")
def fixture_path():
    def builder(relpath):
        return relative_to_this_test_folder(os.path.join("fixtures", relpath))

    return builder


@pytest.fixture(scope="function")
def temp_cache_dir(request):
    temp_directory = tempfile.mkdtemp(prefix="cache_repo_", suffix="_test")

    def fin():
        shutil.rmtree(temp_directory)

    request.addfinalizer(fin)

    return temp_directory


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
def genomic_resource_fixture_dir_repo(fixture_dirname):
    repo_dir = fixture_dirname("genomic_resources")
    return GenomicResourceDirRepo(
        "genomic_resource_fixture_dir_repo", repo_dir)


@pytest.fixture
def genomic_resource_fixture_http_repo(resources_http_server):
    http_port = resources_http_server.http_port
    url = f"http://localhost:{http_port}"
    return GenomicResourceURLRepo("genomic_resource_fixture_url_repo", url)


@pytest.fixture
def genomic_resource_fixture_s3_repo(genomic_resource_fixture_dir_repo, s3):
    src_dir = genomic_resource_fixture_dir_repo.directory
    s3_path = "s3://test-bucket"
    for root, _, files in os.walk(src_dir):
        for fname in files:
            root_rel = os.path.relpath(root, src_dir)
            if root_rel == ".":
                root_rel = ""
            s3.put(
                os.path.join(root, fname),
                os.path.join(s3_path, root_rel, fname))

    repo = GenomicResourceURLRepo("genomic_resource_fixture_url_repo", s3_path)
    repo.filesystem = s3
    return repo


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


def tabix_to_resource(tabix_source, proto, resource_id, filename):

    res = proto.get_resource(resource_id)
    tabix_filename, index_filename = tabix_source
    with proto.open_raw_file(res, filename, "wb") as outfile, \
            open(tabix_filename, "rb") as infile:
        data = infile.read()
        outfile.write(data)

    with proto.open_raw_file(res, f"{filename}.tbi", "wb") as outfile, \
            open(index_filename, "rb") as infile:
        data = infile.read()
        outfile.write(data)

    proto.save_manifest(res, proto.build_manifest(res))
    proto.invalidate()
    proto.build_content_file()


@pytest.fixture
def embedded_content():
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
def embedded_proto(embedded_content, tmp_path, tabix_file):

    def builder(path=tmp_path):
        proto = build_embedded_protocol(
            "src", str(path), content=embedded_content)

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
            proto=proto,
            resource_id="one",
            filename="test.txt.gz")

        return proto
    return builder


@pytest.fixture
def fsspec_proto(
        request,
        embedded_proto, tmp_path_factory,
        s3_base,  # pylint: disable=unused-argument
        http_server):

    def builder(scheme="file"):
        tmp_dir = tmp_path_factory.mktemp(
            basename="fsspec", numbered=True)
        src_proto = embedded_proto(tmp_dir)

        def fin():
            for fname in glob.glob("*.tbi"):
                os.remove(fname)

        request.addfinalizer(fin)

        if scheme == "file":

            tmp_dir = tmp_path_factory.mktemp(
                basename="file", numbered=True)
            proto = build_fsspec_protocol("test", f"file://{tmp_dir}")
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
                "test", f"s3://test-bucket{tmp_dir}",
                endpoint_url=endpoint_url)

            for res in src_proto.get_all_resources():
                proto.copy_resource(res)

            proto.filesystem.invalidate_cache()
            return proto

        if scheme == "http":
            tmp_dir = tmp_path_factory.mktemp(
                basename="http", numbered=True)

            proto = build_fsspec_protocol("test", f"file://{tmp_dir}")
            for res in src_proto.get_all_resources():
                proto.copy_resource(res)
            proto.build_content_file()

            http_server(str(tmp_dir))
            proto = build_fsspec_protocol("test", "http://127.0.0.1:16510")

            proto.filesystem.invalidate_cache()
            return proto

        raise ValueError(f"unsupported scheme: {scheme}")

    return builder
