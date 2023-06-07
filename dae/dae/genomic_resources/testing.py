"""Provides tools usefult for testing."""
from __future__ import annotations
import os
import contextlib
import pathlib
import logging
import threading
import tempfile
import gzip
import importlib
import textwrap

from typing import Any, Dict, Union, cast, Generator, \
    Tuple, ContextManager, List
from collections.abc import Callable
import multiprocessing as mp

from http.server import HTTPServer  # ThreadingHTTPServer

from functools import partial

import pysam

from dae.genomic_resources.repository import \
    GenomicResource, \
    GenomicResourceProtocolRepo, \
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


def setup_gzip(gzip_path: pathlib.Path, gzip_content: str):
    """Set up a gzipped TSV file."""
    content = convert_to_tab_separated(gzip_content)
    out_path = gzip_path
    if gzip_path.suffix != ".gz":
        out_path = gzip_path.with_suffix("gz")
    with gzip.open(out_path, "wt") as outfile:
        outfile.write(content)
    return out_path


def setup_vcf(out_path: pathlib.Path, content: str, csi=False):
    """Set up a VCF file using the content."""
    vcf_data = convert_to_tab_separated(content)
    vcf_path = out_path
    if out_path.suffix == ".gz":
        vcf_path = out_path.with_suffix("")

    assert vcf_path.suffix == ".vcf"
    header_path = vcf_path.with_suffix("")
    header_path = header_path.parent / f"{header_path.name}.header.vcf"

    setup_directories(vcf_path, vcf_data)

    # pylint: disable=no-member
    if out_path.suffix == ".gz":
        vcf_gz_filename = str(vcf_path.parent / f"{vcf_path.name}.gz")
        pysam.tabix_compress(str(vcf_path), vcf_gz_filename)
        pysam.tabix_index(vcf_gz_filename, preset="vcf", csi=csi)

    with pysam.VariantFile(str(out_path)) as variant_file:
        header = variant_file.header
        with open(header_path, "wt", encoding="utf8") as outfile:
            outfile.write(str(header))

    if out_path.suffix == ".gz":
        header_gz_filename = str(header_path.parent / f"{header_path.name}.gz")
        pysam.tabix_compress(str(header_path), header_gz_filename)
        pysam.tabix_index(header_gz_filename, preset="vcf")
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

    setup_directories(out_path.parent, {
        "genomic_resource.yaml": textwrap.dedent(f"""
            type: genome

            filename: {out_path.name}
        """)
    })
    # pylint: disable=import-outside-toplevel
    from dae.genomic_resources.reference_genome import \
        build_reference_genome_from_file
    return build_reference_genome_from_file(str(out_path)).open()


def setup_gene_models(out_path: pathlib.Path, content, fileformat=None):
    """Set up gene models in refflat format using the passed content."""
    setup_directories(out_path, convert_to_tab_separated(content))
    setup_directories(out_path.parent, {
        "genomic_resource.yaml": textwrap.dedent(f"""
            type: gene_models 

            filename: { out_path.name }

            format: "{ fileformat }"
        """)
    })
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


def build_inmemory_protocol(
        proto_id: str,
        root_path: str,
        content: Dict[str, Any]) -> FsspecReadWriteProtocol:
    """Build and return an embedded fsspec protocol for testing."""
    if not os.path.isabs(root_path):
        logger.error(
            "for embedded resources repository we expects an "
            "absolute path: %s", root_path)
        raise ValueError(f"not an absolute root path: {root_path}")

    proto = cast(
        FsspecReadWriteProtocol,
        build_fsspec_protocol(proto_id, f"memory://{root_path}"))
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


def build_inmemory_test_protocol(
        content: Dict[str, Any]) -> FsspecReadWriteProtocol:
    """Build and return an embedded fsspec protocol for testing."""
    with tempfile.TemporaryDirectory("embedded_test_protocol") as root_path:
        proto = build_inmemory_protocol(root_path, root_path, content)
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
        root_path: pathlib.Path, repair=True) -> FsspecReadWriteProtocol:
    """Build and return an filesystem fsspec protocol for testing.

    The root_path is expected to point to a directory structure with all the
    resources.
    """
    proto = cast(
        FsspecReadWriteProtocol,
        build_fsspec_protocol(str(root_path), str(root_path)))
    if repair:
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


@contextlib.contextmanager
def http_threaded_test_server(
        path: pathlib.Path) -> Generator[str, None, None]:
    """Run a range HTTP threaded server.

    The HTTP range server is used to serve directory pointed by root_path.
    """
    # pylint: disable=import-outside-toplevel
    from RangeHTTPServer import RangeRequestHandler  # type: ignore
    handler_class = partial(
        RangeRequestHandler, directory=str(path))
    handler_class.protocol_version = "HTTP/1.0"  # type: ignore
    httpd = HTTPServer(("", 0), handler_class)
    server_address = httpd.server_address
    logger.info(
        "HTTP range server at %s serving %s",
        server_address, path)
    server_thread = threading.Thread(target=httpd.serve_forever)
    server_thread.daemon = True
    server_thread.start()

    yield f"http://{server_address[0]}:{server_address[1]}"  # type: ignore

    logger.info("shutting down HTTP range server %s", server_address)
    httpd.socket.close()
    httpd.shutdown()
    server_thread.join()


@contextlib.contextmanager
def http_process_test_server(path) -> Generator[str, None, None]:
    with _process_server_manager(http_threaded_test_server, path) as http_url:
        yield http_url


@contextlib.contextmanager
def build_http_test_protocol(
        root_path: pathlib.Path, repair=True) -> Generator[
            FsspecReadOnlyProtocol, None, None]:
    """Run an HTTP range server and construct genomic resource protocol.

    The HTTP range server is used to serve directory pointed by root_path.
    This directory should be a valid filesystem genomic resource repository.
    """
    build_filesystem_test_protocol(root_path, repair=repair)

    with http_process_test_server(root_path) as server_address:
        proto = cast(
            FsspecReadOnlyProtocol,
            build_fsspec_protocol(str(root_path), server_address))

        yield proto


def _internal_process_runner(
        module_name: str, server_manager_name: str, args: List[Any],
        start_queue: mp.Queue, stop_queue: mp.Queue):
    module = importlib.import_module(module_name)
    server_manager = getattr(module, server_manager_name)
    try:
        with server_manager(*args) as start_message:
            logger.info("process server started")
            start_queue.put(start_message)
            stop_queue.get()
        logger.info("process server stopped")
    except Exception as ex:  # pylint: disable=broad-except
        start_queue.put(ex)
    else:
        start_queue.put(None)


@contextlib.contextmanager
def _process_server_manager(
        server_manager: Callable[..., ContextManager[str]],
        *args):
    """Run a process server."""
    start_queue: mp.Queue = mp.Queue()
    stop_queue: mp.Queue = mp.Queue()
    proc = mp.Process(
        target=_internal_process_runner,
        args=(
            server_manager.__module__, server_manager.__name__, args,
            start_queue, stop_queue))
    proc.start()

    # wait for start message
    start_message = start_queue.get()
    if isinstance(start_message, Exception):
        logger.error(
            "unexpected execption in starting process: %s", start_message)
        raise start_message

    yield start_message

    # stop the server process
    stop_queue.put("stop")
    stop_queue.close()
    start_queue.close()
    proc.join()


@contextlib.contextmanager
def s3_threaded_test_server() -> Generator[str, None, None]:
    """Run threaded s3 moto server."""
    # pylint: disable=protected-access,import-outside-toplevel
    from moto.server import ThreadedMotoServer  # type: ignore
    server = ThreadedMotoServer(ip_address="", port=0)
    server.start()
    server_address = server._server.server_address
    endpoint_url = f"http://{server_address[0]}:{server_address[1]}"

    yield endpoint_url

    logger.info(
        "Stopping S3 Moto thread at %s", endpoint_url)
    server.stop()
    logger.info(
        "[DONE] Stopping S3 Moto thread at %s", endpoint_url)


@contextlib.contextmanager
def s3_process_test_server() -> Generator[str, None, None]:
    with _process_server_manager(s3_threaded_test_server) as endpoint_url:
        yield endpoint_url


def s3_test_protocol(endpoint_url: str) -> FsspecReadWriteProtocol:
    """Build an S3 fsspec testing protocol on top of existing S3 server."""
    bucket_url = build_s3_test_bucket(endpoint_url)
    proto = cast(
        FsspecReadWriteProtocol,
        build_fsspec_protocol(
            str(bucket_url), bucket_url, endpoint_url=endpoint_url))
    return proto


def build_s3_test_bucket(endpoint_url: str) -> str:
    """Create an s3 test buckent."""
    with tempfile.TemporaryDirectory("s3_test_bucket") as tmp_path:
        # pylint: disable=import-outside-toplevel
        from s3fs.core import S3FileSystem  # type: ignore
        if "AWS_SECRET_ACCESS_KEY" not in os.environ:
            os.environ["AWS_SECRET_ACCESS_KEY"] = "foo"
        if "AWS_ACCESS_KEY_ID" not in os.environ:
            os.environ["AWS_ACCESS_KEY_ID"] = "foo"
        S3FileSystem.clear_instance_cache()
        s3filesystem = S3FileSystem(
            anon=False, client_kwargs={"endpoint_url": endpoint_url})
        s3filesystem.invalidate_cache()
        bucket_url = f"s3:/{tmp_path}"
        s3filesystem.mkdir(bucket_url, acl="public-read")
        logger.warning(
            "S3 moto server at %s with bucket %s",
            endpoint_url, bucket_url)
        return bucket_url


@contextlib.contextmanager
def build_s3_test_server() -> Generator[
        Tuple[str, str], None, None]:
    """Run an S3 moto server."""
    with s3_process_test_server() as endpoint_url:
        bucket_url = build_s3_test_bucket(endpoint_url)
        yield (bucket_url, endpoint_url)


@contextlib.contextmanager
def build_s3_test_protocol(root_path) -> Generator[
        FsspecReadWriteProtocol, None, None]:
    """Run an S3 moto server and construct fsspec genomic resource protocol.

    The S3 moto server is populated with resource from filesystem GRR pointed
    by the root_path.
    """
    # pylint: disable=protected-access,import-outside-toplevel

    with s3_process_test_server() as endpoint_url:
        bucket_url = build_s3_test_bucket(endpoint_url)

        proto = cast(
            FsspecReadWriteProtocol,
            build_fsspec_protocol(
                str(bucket_url), bucket_url, endpoint_url=endpoint_url))
        copy_proto_genomic_resources(
            proto,
            build_filesystem_test_protocol(root_path))

        yield proto


def copy_proto_genomic_resources(
        dest_proto: FsspecReadWriteProtocol,
        src_proto: FsspecReadOnlyProtocol):
    for res in src_proto.get_all_resources():
        dest_proto.copy_resource(res)
    dest_proto.build_content_file()
    dest_proto.filesystem.invalidate_cache()


@contextlib.contextmanager
def proto_builder(
        scheme: str, content: dict) -> Generator[
            Union[FsspecReadOnlyProtocol, FsspecReadWriteProtocol],
            None, None]:
    """Build a test genomic resource protocol with specified content."""
    with tempfile.TemporaryDirectory("s3_test_bucket") as tmp_path:
        root_path = pathlib.Path(tmp_path)
        setup_directories(root_path, content)

        if scheme == "file":
            yield build_filesystem_test_protocol(root_path)
            return
        if scheme == "s3":
            with build_s3_test_protocol(root_path) as proto:
                yield proto
            return
        if scheme == "http":
            with build_http_test_protocol(root_path) as proto:
                yield proto
            return

    raise ValueError(f"unexpected protocol scheme: <{scheme}>")


@contextlib.contextmanager
def resource_builder(
        scheme: str, content: dict) -> Generator[GenomicResource, None, None]:
    with proto_builder(scheme, content) as proto:
        res = proto.get_resource("")
        yield res
