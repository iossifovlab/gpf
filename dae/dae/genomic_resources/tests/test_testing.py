# pylint: disable=W0621,C0114,C0116,C0415,W0212,W0613,C0302,C0115,W0102,W0603
import os
import textwrap
import pytest

from dae.genomic_resources.testing import setup_tabix, \
    build_inmemory_test_protocol, build_inmemory_test_resource, \
    setup_directories, build_filesystem_test_resource, \
    build_http_test_protocol, build_s3_test_protocol


@pytest.fixture(scope="session")
def s3_moto_server_url():
    """Start a moto (i.e. mocked) s3 server and return its URL."""
    # pylint: disable=protected-access,import-outside-toplevel
    if "AWS_SECRET_ACCESS_KEY" not in os.environ:
        os.environ["AWS_SECRET_ACCESS_KEY"] = "foo"
    if "AWS_ACCESS_KEY_ID" not in os.environ:
        os.environ["AWS_ACCESS_KEY_ID"] = "foo"
    from moto.server import ThreadedMotoServer  # type: ignore
    server = ThreadedMotoServer(ip_address="", port=0)
    server.start()
    server_address = server._server.server_address

    yield f"http://{server_address[0]}:{server_address[1]}"

    server.stop()


@pytest.fixture(scope="session")
def s3_client(s3_moto_server_url):
    """Return a boto client connected to the moto server."""
    from botocore.session import Session  # type: ignore

    session = Session()
    client = session.create_client("s3", endpoint_url=s3_moto_server_url)
    return client


@pytest.fixture()
def s3_filesystem(s3_moto_server_url):
    from s3fs.core import S3FileSystem  # type: ignore

    S3FileSystem.clear_instance_cache()
    s3 = S3FileSystem(anon=False,
                      client_kwargs={"endpoint_url": s3_moto_server_url})
    s3.invalidate_cache()
    yield s3


@pytest.fixture()
def s3_tmp_bucket_url(s3_client, s3_filesystem):
    """Create a bucket called 'test-bucket' and return its URL."""
    bucket_url = "s3://test-bucket"
    s3_filesystem.mkdir(bucket_url, acl="public-read")

    yield bucket_url

    s3_filesystem.rm("s3://test-bucket", recursive=True)


def test_setup_tabix(tmp_path):
    tabix_filename, index_filename = setup_tabix(
        tmp_path / "data.txt",
        """
        #chrom pos_begin  pos_end  reference  alternative  s1
        1      10         15       A          G            0.021
        1      16         19       C          G            0.031
        1      16         19       C          A            0.051
        2      10         15       A          G            0.022
        2      16         19       C          G            0.032
        2      16         19       C          A            0.052
        """,
        seq_col=0, start_col=1, end_col=2
    )
    assert tabix_filename.endswith(".gz")
    assert index_filename.endswith(".gz.tbi")


def test_build_inmemory_test_protocol():
    proto = build_inmemory_test_protocol({
        "res1": {
            "genomic_resource.yaml": textwrap.dedent("""
                type: position_score
                table:
                    filename: data.txt
                scores:
                    - id: aaaa
                      type: float
                      desc: ""
                      name: sc
            """),
            "data.txt": """
            #chrom start end sc
            1      10    12  1.1
            2      13    14  1.2
            """
        }
    })
    res = proto.get_resource("res1")
    assert res.get_type() == "position_score"


def test_build_inmemory_test_resource():
    res = build_inmemory_test_resource({
        "genomic_resource.yaml": textwrap.dedent("""
            type: position_score
            table:
                filename: data.txt
            scores:
                - id: aaaa
                  type: float
                  desc: ""
                  name: sc
        """),
        "data.txt": """
        #chrom start end sc
        1      10    12  1.1
        2      13    14  1.2
        """
    })
    assert res.get_type() == "position_score"


@pytest.fixture
def np_score_directory(tmp_path_factory):
    root_path = tmp_path_factory.mktemp("np_score_resource")
    tabix_filename, _ = setup_tabix(
        root_path / "data.txt",
        """
        #chrom pos_begin  pos_end  reference  alternative  s1
        1      10         15       A          G            0.021
        1      16         19       C          G            0.031
        1      16         19       C          A            0.051
        2      10         15       A          G            0.022
        2      16         19       C          G            0.032
        2      16         19       C          A            0.052
        """,
        seq_col=0, start_col=1, end_col=2
    )
    setup_directories(root_path, {
        "genomic_resource.yaml": f"""
          type: np_score
          table:
            filename: {tabix_filename}
          scores:
            - id: cadd_raw
              type: float
              desc: ""
              name: s1
        """,
    })
    return root_path


def test_build_filesystem_resource(np_score_directory):

    res = build_filesystem_test_resource(np_score_directory)
    assert res.get_type() == "np_score"


def test_build_http_test_proto(np_score_directory):

    with build_http_test_protocol(np_score_directory) as proto:
        res = proto.get_resource("")
        assert res.get_type() == "np_score"


def test_build_s3_test_proto(np_score_directory):

    with build_s3_test_protocol(np_score_directory) as proto:
        res = proto.get_resource("")
        assert res.get_type() == "np_score"
