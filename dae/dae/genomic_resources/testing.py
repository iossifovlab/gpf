"""Provides tools usefult for testing."""
from __future__ import annotations
import contextlib
import pathlib
import time

import logging
import threading
import multiprocessing

from http.server import HTTPServer  # ThreadingHTTPServer

from typing import Any, cast, Optional, Dict
from functools import partial

from dae.genomic_resources.repository import \
    GenomicResource, \
    GenomicResourceProtocolRepo, \
    ReadWriteRepositoryProtocol, \
    parse_gr_id_version_token, \
    is_gr_id_token, \
    GR_CONF_FILE_NAME
from dae.genomic_resources.fsspec_protocol import \
    FsspecReadWriteProtocol, \
    build_fsspec_protocol


logger = logging.getLogger(__name__)


def _scan_for_resource_files(content_dict: dict[str, Any], parent_dirs):

    for path, content in content_dict.items():
        if isinstance(content, dict):
            # handle subdirectory
            for fname, fcontent in _scan_for_resource_files(
                    content, [*parent_dirs, path]):
                yield fname, fcontent
        else:
            fname = "/".join([*parent_dirs, path])
            if isinstance(content, (str, bytes)):
                # handle file content
                yield fname, content
            else:
                logger.error(
                    "unexpected content at %s: %s", fname, content)
                raise ValueError(f"unexpected content at {fname}: {content}")


def _scan_for_resources(content_dict, parent_id):
    name = "/".join(parent_id)
    id_ver = parse_gr_id_version_token(name)
    if isinstance(content_dict, dict) and id_ver and \
            GR_CONF_FILE_NAME in content_dict and \
            not isinstance(content_dict[GR_CONF_FILE_NAME], dict):
        # resource found
        resource_id, version = id_ver
        yield "/".join([*parent_id, resource_id]), version, content_dict
        return

    for name, content in content_dict.items():
        id_ver = parse_gr_id_version_token(name)
        if isinstance(content, dict) and id_ver and \
                GR_CONF_FILE_NAME in content and \
                not isinstance(content[GR_CONF_FILE_NAME], dict):
            # resource found
            resource_id, version = id_ver
            yield "/".join([*parent_id, resource_id]), version, content
        else:
            curr_id = parent_id + [name]
            curr_id_path = "/".join(curr_id)
            if not isinstance(content, dict):
                logger.warning("file <%s> is not used.", curr_id_path)
                continue
            if not is_gr_id_token(name):
                logger.warning(
                    "directory <%s> has a name <%s> that is not a "
                    "valid Genomic Resource Id Token.", curr_id_path, name)
                continue

            # scan children
            for rid, rver, rcontent in _scan_for_resources(content, curr_id):
                yield rid, rver, rcontent


def build_testing_protocol(
        content: Optional[dict[str, Any]],
        scheme: str = "memory",
        proto_id: str = "testing",
        root_path: str = "/testing",
        **kwargs) -> ReadWriteRepositoryProtocol:
    """Create an embedded or dir GRR protocol using passed content."""
    if content is None:
        content = {}

    if not root_path.startswith("/"):
        root_path = f"/{root_path}"

    if scheme == "memory":
        proto = build_fsspec_protocol(
            proto_id, f"memory://{root_path}", **kwargs)
    elif scheme == "file":
        proto = build_fsspec_protocol(
            proto_id, f"file://{root_path}", **kwargs)
    else:
        raise ValueError(f"unsupported testing protocol: {scheme}")

    proto = cast(FsspecReadWriteProtocol, proto)

    for rid, rver, rcontent in _scan_for_resources(content, []):
        resource = GenomicResource(rid, rver, proto)
        for fname, fcontent in _scan_for_resource_files(rcontent, []):
            mode = "wt"
            if isinstance(fcontent, bytes):
                mode = "wb"
            with proto.open_raw_file(resource, fname, mode) as outfile:
                outfile.write(fcontent)
            proto.save_resource_file_state(
                resource, proto.build_resource_file_state(resource, fname))

        proto.save_manifest(resource, proto.build_manifest(resource))

    return proto


def build_testing_repository(
        content: dict[str, Any],
        scheme: str = "memory",
        repo_id: str = "testing",
        root_path: str = "/testing",
        **kwargs) -> GenomicResourceProtocolRepo:
    """Create an embedded or dir GRR repository using passed content."""
    proto = build_testing_protocol(
        content, scheme=scheme, proto_id=repo_id,
        root_path=root_path, **kwargs)

    return GenomicResourceProtocolRepo(proto)


def build_test_resource(
        content: dict,
        scheme="memory",
        repo_id="testing",
        root_path="/testing",
        **kwargs) -> GenomicResource:
    """Create a resource based on content passed."""
    repo = build_testing_repository(
        content,
        # content={
        #     "t": content
        # },
        scheme=scheme,
        repo_id=repo_id,
        root_path=root_path,
        **kwargs)
    return repo.get_resource("")


def tabix_to_resource(tabix_source, resource, filename, update_repo=True):
    """Store a tabix file into a resource."""
    tabix_filename, index_filename = tabix_source
    proto = resource.proto

    with proto.open_raw_file(resource, filename, "wb") as outfile, \
            open(tabix_filename, "rb") as infile:
        data = infile.read()
        outfile.write(data)

    with proto.open_raw_file(resource, f"{filename}.tbi", "wb") as outfile, \
            open(index_filename, "rb") as infile:
        data = infile.read()
        outfile.write(data)

    if update_repo:
        proto.save_manifest(resource, proto.build_manifest(resource))
        proto.invalidate()
        proto.build_content_file()


def range_http_thread_server_generator(directory):
    """Return threading HTTP range server generator for testing."""
    # pylint: disable=import-outside-toplevel
    from RangeHTTPServer import RangeRequestHandler  # type: ignore

    handler_class = partial(
        RangeRequestHandler, directory=directory)
    handler_class.protocol_version = "HTTP/1.0"
    httpd = HTTPServer(("", 0), handler_class)
    try:
        server_address = httpd.server_address
        logger.info(
            "HTTP range server at %s serving %s",
            server_address, directory)
        server_thread = threading.Thread(target=httpd.serve_forever)
        server_thread.daemon = True
        server_thread.start()
        yield f"http://{server_address[0]}:{server_address[1]}"

    finally:
        time.sleep(0.1)
        logger.info("shutting down HTT range server %s", server_address)
        httpd.socket.close()
        httpd.shutdown()
        server_thread.join()


def range_http_process_server_generator(directory):
    """Return process HTTP range server generator for testing."""
    # pylint: disable=import-outside-toplevel
    from RangeHTTPServer import RangeRequestHandler  # type: ignore

    def runner(queue):
        handler_class = partial(
            RangeRequestHandler, directory=directory)
        handler_class.protocol_version = "HTTP/1.0"
        httpd = HTTPServer(("", 0), handler_class)
        try:
            server_address = httpd.server_address
            queue.put(f"http://{server_address[0]}:{server_address[1]}")
            logger.info(
                "HTTP range server at %s serving %s",
                server_address, directory)
            server_thread = threading.Thread(target=httpd.serve_forever)
            server_thread.daemon = True
            server_thread.start()

            while 1:
                command = queue.get()
                if command == "stop":
                    break
        finally:
            time.sleep(0.1)
            logger.info("shutting down HTT range server %s", server_address)
            httpd.socket.close()
            httpd.shutdown()
            server_thread.join()

    queue = multiprocessing.Queue()
    proc = multiprocessing.Process(target=runner, args=(queue, ))
    proc.start()
    # wait for server address
    server_address = queue.get()
    yield server_address

    # stop the server process
    queue.put("stop")


@contextlib.contextmanager
def range_http_serve(directory):
    yield from range_http_process_server_generator(directory=directory)


def setup_directories(
        root_dir: pathlib.Path, content: Dict[str, Any]) -> None:
    """Set up directory and subdirectory structures using the content."""
    root_dir = pathlib.Path(root_dir)

    root_dir.mkdir(parents=True, exist_ok=True)
    for path_name, path_content in content.items():
        if isinstance(path_content, str):
            (root_dir / path_name).write_text(path_content, encoding="utf8")
        elif isinstance(path_content, dict):
            setup_directories(root_dir / path_name, path_content)
        else:
            raise ValueError(
                f"unexpected content type: {path_content} for {path_name}")


def convert_to_tab_separated(content: str):
    """Convert a string into tab separated file content.

    Useful for testing purposes.
    """
    result = "\n".join(
        "\t".join(line.strip("\n\r").split())
        for line in content.split("\n")
        if line.strip("\r\n") != "")
    result = result.replace("||", " ")
    # result = result.replace("EMPTY", "")
    return result
