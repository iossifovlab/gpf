"""Provides tools usefult for testing."""
from __future__ import annotations
import os
import contextlib
import time
import pathlib
import logging
import threading
import tempfile
from typing import Any, Dict, Union, cast, Optional, Generator
from multiprocessing import Queue, Process

from http.server import HTTPServer  # ThreadingHTTPServer

from functools import partial

import pysam

from dae.genomic_resources.repository import \
    GenomicResource, \
    GenomicResourceProtocolRepo, \
    ReadWriteRepositoryProtocol, \
    parse_gr_id_version_token, \
    is_gr_id_token, \
    GR_CONF_FILE_NAME
from dae.genomic_resources.fsspec_protocol import \
    FsspecReadWriteProtocol, FsspecReadOnlyProtocol, \
    build_fsspec_protocol


logger = logging.getLogger(__name__)


def convert_to_tab_separated(content: str):
    """Convert a string into tab separated file content.

    Useful for testing purposes.
    If you need to have a space in the file content use '||'.
    """
    result = []
    for line in content.split("\n"):
        line = line.strip("\n\r")
        if not line:
            continue
        if line.startswith("##"):
            result.append(line)
        else:
            result.append("\t".join(line.split()))
    text = "\n".join(result)
    return text.replace("||", " ")


def setup_directories(
        root_dir: pathlib.Path,
        content: Union[str, Dict[str, Any]]) -> None:
    """Set up directory and subdirectory structures using the content."""
    root_dir = pathlib.Path(root_dir)
    root_dir.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(content, str):
        root_dir.write_text(content, encoding="utf8")
    elif isinstance(content, dict):
        for path_name, path_content in content.items():
            setup_directories(root_dir / path_name, path_content)
    else:
        raise ValueError(
            f"unexpected content type: {content} for {root_dir}")


def setup_pedigree(ped_path, content):
    ped_data = convert_to_tab_separated(content)
    setup_directories(ped_path, ped_data)
    return str(ped_path)


def setup_denovo(denovo_path, content):
    denovo_data = convert_to_tab_separated(content)
    setup_directories(denovo_path, denovo_data)
    return str(denovo_path)


def setup_tabix(tabix_path: pathlib.Path, tabix_content: str, **kwargs):
    """Set up a tabix file."""
    content = convert_to_tab_separated(tabix_content)
    out_path = tabix_path
    if tabix_path.suffix == ".gz":
        out_path = tabix_path.with_suffix("")
    setup_directories(out_path, content)

    tabix_filename = str(out_path.parent / f"{out_path.name}.gz")
    index_filename = f"{tabix_filename}.tbi"
    force = kwargs.pop("force", False)
    # pylint: disable=no-member
    pysam.tabix_compress(str(out_path), tabix_filename, force=force)
    pysam.tabix_index(tabix_filename, force=force, **kwargs)

    out_path.unlink()

    return tabix_filename, index_filename


def setup_vcf(out_path: pathlib.Path, content: str):
    """Set up a VCF file using the content."""
    vcf_data = convert_to_tab_separated(content)
    vcf_path = out_path
    if out_path.suffix == ".gz":
        vcf_path = out_path.with_suffix("")

    setup_directories(vcf_path, vcf_data)

    if out_path.suffix == ".gz":
        vcf_gz_filename = str(vcf_path.parent / f"{vcf_path.name}.gz")
        # pylint: disable=no-member
        pysam.tabix_compress(str(vcf_path), vcf_gz_filename)
        pysam.tabix_index(vcf_gz_filename, preset="vcf")

    return str(out_path)


def setup_dae_transmitted(root_path, summary_content, toomany_content):
    """Set up a DAE transmitted variants file using passed content."""
    summary = convert_to_tab_separated(summary_content)
    toomany = convert_to_tab_separated(toomany_content)

    setup_directories(root_path, {
        "dae_transmitted_data": {
            "tr.txt": summary,
            "tr-TOOMANY.txt": toomany
        }
    })

    # pylint: disable=no-member
    pysam.tabix_compress(
        str(root_path / "dae_transmitted_data" / "tr.txt"),
        str(root_path / "dae_transmitted_data" / "tr.txt.gz"))
    pysam.tabix_compress(
        str(root_path / "dae_transmitted_data" / "tr-TOOMANY.txt"),
        str(root_path / "dae_transmitted_data" / "tr-TOOMANY.txt.gz"))

    pysam.tabix_index(
        str(root_path / "dae_transmitted_data" / "tr.txt.gz"),
        seq_col=0, start_col=1, end_col=1, line_skip=1)
    pysam.tabix_index(
        str(root_path / "dae_transmitted_data" / "tr-TOOMANY.txt.gz"),
        seq_col=0, start_col=1, end_col=1, line_skip=1)

    return (str(root_path / "dae_transmitted_data" / "tr.txt.gz"),
            str(root_path / "dae_transmitted_data" / "tr-TOOMANY.txt.gz"))


def setup_genome(out_path: pathlib.Path, content):
    """Set up reference genome using the content."""
    if out_path.suffix != ".fa":
        raise ValueError("genome output file is expected to have '.fa' suffix")
    setup_directories(out_path, convert_to_tab_separated(content))

    # pylint: disable=no-member
    pysam.faidx(str(out_path))  # type: ignore

    # pylint: disable=import-outside-toplevel
    from dae.genomic_resources.reference_genome import \
        build_reference_genome_from_file
    return build_reference_genome_from_file(str(out_path)).open()


def setup_gene_models(out_path: pathlib.Path, content, fileformat=None):
    """Set up gene models in refflat format using the passed content."""
    setup_directories(out_path, convert_to_tab_separated(content))
    # pylint: disable=import-outside-toplevel
    from dae.genomic_resources.gene_models import build_gene_models_from_file
    return build_gene_models_from_file(str(out_path), fileformat=fileformat)


def setup_empty_gene_models(out_path: pathlib.Path):
    """Set up empty gene models."""
    content = """
#geneName name chrom strand txStart txEnd cdsStart cdsEnd exonCount exonStarts exonEnds
    """  # noqa
    return setup_gene_models(out_path, content, fileformat="refflat")


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


def build_inmemory_test_protocol(
        content: Dict[str, Any]) -> FsspecReadWriteProtocol:
    """Build and return an embedded fsspec protocol for testing."""
    with tempfile.TemporaryDirectory("embedded_test_protocol") as root_path:

        proto = cast(
            FsspecReadWriteProtocol,
            build_fsspec_protocol(root_path, f"memory://{root_path}"))
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


def build_inmemory_test_repository(
        content: dict[str, Any]) -> GenomicResourceProtocolRepo:
    """Create an embedded GRR repository using passed content."""
    proto = build_inmemory_test_protocol(content)
    return GenomicResourceProtocolRepo(proto)


def build_inmemory_test_resource(
        content: dict[str, Any]) -> GenomicResource:
    """Create a test resource based on content passed.

    The passed content should appropriate for a single resource.
    Example content:
    {
        "genomic_resource.yaml": textwrap.dedent('''
            type: position_score
            table:
                filename: data.txt
            scores:
                - id: aaaa
                    type: float
                    desc: ""
                    name: sc
        '''),
        "data.txt": convert_to_tab_separated('''
            #chrom start end sc
            1      10    12  1.1
            2      13    14  1.2
        ''')
    }
    """
    proto = build_inmemory_test_protocol(content)
    return proto.get_resource("")


def build_filesystem_test_protocol(
        root_path: pathlib.Path) -> FsspecReadWriteProtocol:
    """Build and return an filesystem fsspec protocol for testing.

    The root_path is expected to point to a directory structure with all the
    resources.
    """
    proto = cast(
        FsspecReadWriteProtocol,
        build_fsspec_protocol(str(root_path), str(root_path)))

    for res in proto.get_all_resources():
        proto.save_manifest(res, proto.build_manifest(res))
    proto.build_content_file()
    return proto


def build_filesystem_test_repository(
        root_path: pathlib.Path) -> GenomicResourceProtocolRepo:
    """Build and return an filesystem fsspec repository for testing.

    The root_path is expected to point to a directory structure with all the
    resources.
    """
    proto = build_filesystem_test_protocol(root_path)
    return GenomicResourceProtocolRepo(proto)


def build_filesystem_test_resource(
        root_path: pathlib.Path) -> GenomicResource:
    proto = build_filesystem_test_protocol(root_path)
    return proto.get_resource("")


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
    handler_class.protocol_version = "HTTP/1.0"  # type: ignore
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
        handler_class.protocol_version = "HTTP/1.0"  # type: ignore
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

    queue: Queue = Queue()
    proc = Process(target=runner, args=(queue, ))
    proc.start()
    # wait for server address
    server_address = queue.get()
    yield server_address

    # stop the server process
    queue.put("stop")


@contextlib.contextmanager
def range_http_serve(directory):
    yield from range_http_process_server_generator(directory=directory)


# @contextlib.contextmanager
# def build_http_test_protocol(
#         root_path: pathlib.Path) -> Generator[
#             FsspecReadOnlyProtocol, None, None]:
#     """Run an HTTP range server and construct genomic resource protocol.

#     The HTTP range server is used to serve directory pointed by root_path.
#     This directory should be a valid filesystem genomic resource repository.
#     """
#     # pylint: disable=import-outside-toplevel
#     from RangeHTTPServer import RangeRequestHandler  # type: ignore

#     def runner(queue):
#         handler_class = partial(
#             RangeRequestHandler, directory=str(root_path))
#         handler_class.protocol_version = "HTTP/1.0"  # type: ignore
#         httpd = HTTPServer(("", 0), handler_class)
#         try:
#             server_address = httpd.server_address
#             queue.put(f"http://{server_address[0]}:{server_address[1]}")
#             logger.info(
#                 "HTTP range server at %s serving %s",
#                 server_address, root_path)
#             server_thread = threading.Thread(target=httpd.serve_forever)
#             server_thread.daemon = True
#             server_thread.start()

#             while 1:
#                 command = queue.get(timeout=5.0)
#                 if command == "stop":
#                     break
#         finally:
#             time.sleep(0.1)
#             logger.info("shutting down HTT range server %s", server_address)
#             httpd.socket.close()
#             httpd.shutdown()
#             server_thread.join()

#     build_filesystem_test_protocol(root_path)

#     queue: Queue = Queue()
#     proc = Process(target=runner, args=(queue, ))
#     proc.start()
#     # wait for server address
#     server_address = queue.get(timeout=0.5)
#     proto = cast(
#         FsspecReadOnlyProtocol,
#         build_fsspec_protocol(str(root_path), server_address))

#     yield proto

#     # stop the server process
#     queue.put("stop")


@contextlib.contextmanager
def build_http_test_protocol(
        root_path: pathlib.Path) -> Generator[
            FsspecReadOnlyProtocol, None, None]:
    """Run an HTTP range server and construct fsspec genomic resource protocol.

    The HTTP range server is used to serve directory pointed by root_path.
    This directory should be a valid filesystem genomic resource repository.
    """
    build_filesystem_test_protocol(root_path)

    # pylint: disable=import-outside-toplevel
    from RangeHTTPServer import RangeRequestHandler  # type: ignore

    handler_class = partial(
        RangeRequestHandler, directory=str(root_path))
    handler_class.protocol_version = "HTTP/1.0"  # type: ignore
    httpd = HTTPServer(("", 0), handler_class)
    try:
        server_address = httpd.server_address
        logger.info(
            "HTTP range server at %s serving %s",
            server_address, root_path)
        server_thread = threading.Thread(target=httpd.serve_forever)
        server_thread.daemon = True
        server_thread.start()

        server_url = f"http://{server_address[0]}:{server_address[1]}"
        proto = cast(
            FsspecReadOnlyProtocol,
            build_fsspec_protocol(str(root_path), server_url))

        yield proto

    finally:
        time.sleep(0.1)
        logger.info("shutting down HTT range server %s", server_address)
        httpd.socket.close()
        httpd.shutdown()
        server_thread.join()


@contextlib.contextmanager
def build_s3_test_protocol(
        root_path: pathlib.Path) -> Generator[
            FsspecReadWriteProtocol, None, None]:
    """Run an S3 moto server and construct fsspec genomic resource protocol.

    The S3 moto server is populated with resource from filesystem GRR pointed
    by the root_path.
    """
    src_proto = build_filesystem_test_protocol(root_path)

    # pylint: disable=protected-access,import-outside-toplevel
    if "AWS_SECRET_ACCESS_KEY" not in os.environ:
        os.environ["AWS_SECRET_ACCESS_KEY"] = "foo"
    if "AWS_ACCESS_KEY_ID" not in os.environ:
        os.environ["AWS_ACCESS_KEY_ID"] = "foo"
    from moto.server import ThreadedMotoServer  # type: ignore
    from s3fs.core import S3FileSystem  # type: ignore

    server = ThreadedMotoServer(ip_address="", port=0)
    server.start()
    server_address = server._server.server_address
    endpoint_url = f"http://{server_address[0]}:{server_address[1]}"

    with tempfile.TemporaryDirectory("s3_test_protocol") as tmp_path:

        S3FileSystem.clear_instance_cache()
        s3filesystem = S3FileSystem(
            anon=False, client_kwargs={"endpoint_url": endpoint_url})
        s3filesystem.invalidate_cache()
        bucket_url = f"s3:/{tmp_path}"
        s3filesystem.mkdir(bucket_url, acl="public-read")

        proto = cast(
            FsspecReadWriteProtocol,
            build_fsspec_protocol(
                str(root_path), bucket_url, endpoint_url=endpoint_url))
        for res in src_proto.get_all_resources():
            proto.copy_resource(res)
        proto.filesystem.invalidate_cache()

        yield proto

        server.stop()


def copy_proto_genomic_resources(
        dest_proto: ReadWriteRepositoryProtocol,
        src_proto: FsspecReadOnlyProtocol):
    for res in src_proto.get_all_resources():
        dest_proto.copy_resource(res)
