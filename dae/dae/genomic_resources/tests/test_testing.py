# pylint: disable=W0621,C0114,C0116,C0415,W0212,W0613,C0302,C0115,W0102,W0603
import contextlib
import multiprocessing as mp
import pathlib
import textwrap
from collections.abc import Generator

# import requests
import pytest

from dae.genomic_resources.testing import (
    _internal_process_runner,
    _process_server_manager,
    build_filesystem_test_resource,
    build_http_test_protocol,
    build_inmemory_test_protocol,
    build_inmemory_test_resource,
    setup_directories,
    setup_tabix,
)


def test_setup_tabix(tmp_path: pathlib.Path) -> None:
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
        seq_col=0, start_col=1, end_col=2,
    )
    assert tabix_filename.endswith(".gz")
    assert index_filename.endswith(".gz.tbi")


def test_build_inmemory_test_protocol() -> None:
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
            """,
        },
    })
    res = proto.get_resource("res1")
    assert res.get_type() == "position_score"


def test_build_inmemory_test_resource() -> None:
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
        """,
    })
    assert res.get_type() == "position_score"


@pytest.fixture()
def np_score_directory(tmp_path: pathlib.Path) -> pathlib.Path:
    root_path = tmp_path
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
        seq_col=0, start_col=1, end_col=2,
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


def test_build_filesystem_resource(
        np_score_directory: pathlib.Path) -> None:

    res = build_filesystem_test_resource(np_score_directory)
    assert res.get_type() == "np_score"


def test_build_http_test_proto(
        np_score_directory: pathlib.Path) -> None:

    with build_http_test_protocol(np_score_directory) as proto:
        res = proto.get_resource("")
        assert res.get_type() == "np_score"


# def test_build_s3_test_proto(
#         np_score_directory: pathlib.Path) -> None:

#     with build_s3_test_protocol(np_score_directory) as proto:
#         res = proto.get_resource("")
#         assert res.get_type() == "np_score"


@contextlib.contextmanager
def _server_manager_simple() -> Generator[str, None, None]:
    yield "started"


def test_internal_process_runner() -> None:
    start_queue: mp.Queue = mp.Queue()
    stop_queue: mp.Queue = mp.Queue()
    stop_queue.put("stop")

    _internal_process_runner(
        "dae.genomic_resources.tests.test_testing",
        "_server_manager_simple", [],
        start_queue, stop_queue)
    result = start_queue.get()
    assert result == "started"

    # clean up
    start_queue.close()
    stop_queue.close()
    start_queue.join_thread()
    stop_queue.join_thread()


def test_process_server_simple() -> None:
    with _process_server_manager(_server_manager_simple) as start_message:
        assert start_message == "started"


@contextlib.contextmanager
def _server_manager_start_failed() -> Generator[str, None, None]:
    raise ValueError("unexpected error")


def test_internal_process_runner_start_failed() -> None:
    start_queue: mp.Queue = mp.Queue()
    stop_queue: mp.Queue = mp.Queue()
    stop_queue.put("stop")

    _internal_process_runner(
        "dae.genomic_resources.tests.test_testing",
        "_server_manager_simple", [],
        start_queue, stop_queue)
    result = start_queue.get()
    assert result == "started"

    # clean up
    start_queue.close()
    stop_queue.close()
    start_queue.join_thread()
    stop_queue.join_thread()


def test_process_server_start_failed() -> None:
    with pytest.raises(ValueError):
        with _process_server_manager(
                _server_manager_start_failed) as _:
            pass


@contextlib.contextmanager
def _server_manager_stop_failed() -> Generator[str, None, None]:
    yield "started"
    raise ValueError("unexpected error")


def test_internal_process_runner_stop_failed() -> None:
    start_queue: mp.Queue = mp.Queue()
    stop_queue: mp.Queue = mp.Queue()
    stop_queue.put("stop")

    _internal_process_runner(
        "dae.genomic_resources.tests.test_testing",
        "_server_manager_simple", [],
        start_queue, stop_queue)
    result = start_queue.get()
    assert result == "started"
    start_queue.get()

    # clean up
    start_queue.close()
    stop_queue.close()
    start_queue.join_thread()
    stop_queue.join_thread()


def test_process_server_stop_failed() -> None:
    with _process_server_manager(_server_manager_stop_failed) as start_message:
        assert start_message == "started"


# def test_s3_threaded_server_simple():
#     with s3_threaded_test_server() as endpoint_url:
#         response = requests.get(endpoint_url, timeout=10.0)
#         assert response.status_code == 200

#     with s3_threaded_test_server() as endpoint_url:
#         response = requests.get(endpoint_url, timeout=10.0)
#         assert response.status_code == 200

#     with s3_threaded_test_server() as endpoint_url:
#         response = requests.get(endpoint_url, timeout=10.0)
#         assert response.status_code == 200
