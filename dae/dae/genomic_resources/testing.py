"""Provides tools usefult for testing."""
from __future__ import annotations

import contextlib
import gzip
import importlib
import logging
import multiprocessing as mp
import os
import pathlib
import tempfile
import textwrap
import threading
from collections.abc import Callable, Generator
from contextlib import AbstractContextManager
from functools import partial
from http.server import HTTPServer  # ThreadingHTTPServer
from typing import Any, cast

import pyBigWig  # type: ignore
import pysam
from s3fs.core import S3FileSystem

from dae.genomic_resources.fsspec_protocol import (
    FsspecReadOnlyProtocol,
    FsspecReadWriteProtocol,
    build_fsspec_protocol,
    build_inmemory_protocol,
)
from dae.genomic_resources.gene_models import GeneModels
from dae.genomic_resources.reference_genome import ReferenceGenome
from dae.genomic_resources.repository import (
    GenomicResource,
    GenomicResourceProtocolRepo,
)

logger = logging.getLogger(__name__)


def convert_to_tab_separated(content: str) -> str:
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
    text = text.replace("||", " ")
    return text.replace("EMPTY", ".")


def setup_directories(
        root_dir: pathlib.Path,
        content: str | dict[str, Any]) -> None:
    """Set up directory and subdirectory structures using the content."""
    root_dir = pathlib.Path(root_dir)
    root_dir.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(content, str):
        root_dir.write_text(content, encoding="utf8")
    elif isinstance(content, bytes):
        root_dir.write_bytes(content)
    elif isinstance(content, dict):
        for path_name, path_content in content.items():
            setup_directories(root_dir / path_name, path_content)
    else:
        raise TypeError(
            f"unexpected content type: {content} for {root_dir}")


def setup_pedigree(ped_path: pathlib.Path, content: str) -> pathlib.Path:
    ped_data = convert_to_tab_separated(content)
    setup_directories(ped_path, ped_data)
    return ped_path


def setup_denovo(denovo_path: pathlib.Path, content: str) -> pathlib.Path:
    denovo_data = convert_to_tab_separated(content)
    setup_directories(denovo_path, denovo_data)
    return denovo_path


def setup_tabix(
        tabix_path: pathlib.Path, tabix_content: str,
        **kwargs: bool | str | int) -> tuple[str, str]:
    """Set up a tabix file."""
    content = convert_to_tab_separated(tabix_content)
    out_path = tabix_path
    if tabix_path.suffix == ".gz":
        out_path = tabix_path.with_suffix("")
    setup_directories(out_path, content)

    tabix_filename = str(out_path.parent / f"{out_path.name}.gz")
    index_filename = f"{tabix_filename}.tbi"
    force = cast(bool, kwargs.pop("force", False))
    # pylint: disable=no-member
    pysam.tabix_compress(str(out_path), tabix_filename, force=force)
    pysam.tabix_index(tabix_filename, force=force, **kwargs)  # type: ignore

    out_path.unlink()

    return tabix_filename, index_filename


def setup_gzip(gzip_path: pathlib.Path, gzip_content: str) -> pathlib.Path:
    """Set up a gzipped TSV file."""
    content = convert_to_tab_separated(gzip_content)
    out_path = gzip_path
    if gzip_path.suffix != ".gz":
        out_path = gzip_path.with_suffix("gz")
    with gzip.open(out_path, "wt") as outfile:
        outfile.write(content)
    return out_path


def setup_vcf(
        out_path: pathlib.Path, content: str, *,
        csi: bool = False) -> pathlib.Path:
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
    return out_path


def setup_dae_transmitted(
    root_path: pathlib.Path,
    summary_content: str,
    toomany_content: str,
) -> tuple[pathlib.Path, pathlib.Path]:
    """Set up a DAE transmitted variants file using passed content."""
    summary = convert_to_tab_separated(summary_content)
    toomany = convert_to_tab_separated(toomany_content)

    setup_directories(root_path, {
        "dae_transmitted_data": {
            "tr.txt": summary,
            "tr-TOOMANY.txt": toomany,
        },
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

    return (root_path / "dae_transmitted_data" / "tr.txt.gz",
            root_path / "dae_transmitted_data" / "tr-TOOMANY.txt.gz")


def setup_bigwig(
    out_path: pathlib.Path,
    content: str,
    chrom_lens: dict[str, int],
) -> pathlib.Path:
    """
    Setup a bigwig format variants file using bedGraph-style content.

    Example:
    chr1	0	100	0.0
    chr1	100	120	1.0
    chr1	125	126	200.0
    """
    bw_file = pyBigWig.open(str(out_path), "w")  # pylint: disable=I1101
    bw_file.addHeader(list(chrom_lens.items()), maxZooms=0)

    chrom_col: list[str] = []
    start_col: list[int] = []
    end_col: list[int] = []
    val_col: list[float] = []
    prev_end: int = -1
    for line in convert_to_tab_separated(content).split("\n"):
        tokens = line.strip().split("\t")
        assert len(tokens) == 4
        chrom = tokens[0]
        start = int(tokens[1])
        end = int(tokens[2])
        val = float(tokens[3])

        assert chrom in chrom_lens
        assert start < end
        assert start >= prev_end
        prev_end = end

        chrom_col.append(chrom)
        start_col.append(start)
        end_col.append(end)
        val_col.append(val)

    bw_file.addEntries(chrom_col, start_col, ends=end_col, values=val_col)
    bw_file.close()
    return out_path


def setup_genome(out_path: pathlib.Path, content: str) -> ReferenceGenome:
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
        """),
    })
    # pylint: disable=import-outside-toplevel
    from dae.genomic_resources.reference_genome import (
        build_reference_genome_from_file,
    )
    return build_reference_genome_from_file(str(out_path)).open()


def setup_gene_models(
        out_path: pathlib.Path,
        content: str, fileformat: str | None = None) -> GeneModels:
    """Set up gene models in refflat format using the passed content."""
    setup_directories(out_path, convert_to_tab_separated(content))
    setup_directories(out_path.parent, {
        "genomic_resource.yaml": textwrap.dedent(f"""
            type: gene_models

            filename: { out_path.name }

            format: "{ fileformat }"
        """),
    })
    # pylint: disable=import-outside-toplevel
    from dae.genomic_resources.gene_models import build_gene_models_from_file
    gene_models = build_gene_models_from_file(
        str(out_path), file_format=fileformat)
    gene_models.load()
    return gene_models


def setup_empty_gene_models(out_path: pathlib.Path) -> GeneModels:
    """Set up empty gene models."""
    content = """
#geneName name chrom strand txStart txEnd cdsStart cdsEnd exonCount exonStarts exonEnds
    """  # noqa
    return setup_gene_models(out_path, content, fileformat="refflat")


def build_inmemory_test_protocol(
        content: dict[str, Any]) -> FsspecReadWriteProtocol:
    """Build and return an embedded fsspec protocol for testing."""
    with tempfile.TemporaryDirectory("embedded_test_protocol") as root_path:
        return build_inmemory_protocol(root_path, root_path, content)


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
    root_path: pathlib.Path, *,
    repair: bool = True,
) -> FsspecReadWriteProtocol:
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
def http_process_test_server(path: pathlib.Path) -> Generator[str, None, None]:
    with _process_server_manager(http_threaded_test_server, path) as http_url:
        yield http_url


@contextlib.contextmanager
def build_http_test_protocol(
    root_path: pathlib.Path, *,
    repair: bool = True,
) -> Generator[FsspecReadOnlyProtocol, None, None]:
    """Run an HTTP range server and construct genomic resource protocol.

    The HTTP range server is used to serve directory pointed by root_path.
    This directory should be a valid filesystem genomic resource repository.
    """
    build_filesystem_test_protocol(root_path, repair=repair)

    with http_process_test_server(root_path) as server_address:
        yield build_fsspec_protocol(str(root_path), server_address)


def _internal_process_runner(
        module_name: str, server_manager_name: str, args: list[Any],
        start_queue: mp.Queue, stop_queue: mp.Queue) -> None:
    module = importlib.import_module(module_name)
    server_manager = getattr(module, server_manager_name)
    try:
        with server_manager(*args) as start_message:
            logger.info("process server started")
            start_queue.put(start_message)
            stop_queue.get()
        logger.info("process server stopped")
    except Exception as ex:  # noqa: BLE001 pylint: disable=broad-except
        start_queue.put(ex)
    else:
        start_queue.put(None)


@contextlib.contextmanager
def _process_server_manager(
        server_manager: Callable[..., AbstractContextManager[str]],
        *args: pathlib.Path) -> Generator[str, None, None]:
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


def s3_test_server_endpoint() -> str:
    host = os.environ.get("LOCALSTACK_HOST", "localhost")
    return f"http://{host}:4566"


def s3_test_protocol() -> FsspecReadWriteProtocol:
    """Build an S3 fsspec testing protocol on top of existing S3 server."""
    endpoint_url = s3_test_server_endpoint()
    s3filesystem = build_s3_test_filesystem()
    bucket_url = build_s3_test_bucket(s3filesystem)
    return cast(
        FsspecReadWriteProtocol,
        build_fsspec_protocol(
            str(bucket_url), bucket_url, endpoint_url=endpoint_url))


def build_s3_test_filesystem(
        endpoint_url: str | None = None) -> S3FileSystem:
    """Create an S3 fsspec filesystem connected to the S3 server."""
    if "AWS_SECRET_ACCESS_KEY" not in os.environ:
        os.environ["AWS_SECRET_ACCESS_KEY"] = "foo"  # noqa: S105
    if "AWS_ACCESS_KEY_ID" not in os.environ:
        os.environ["AWS_ACCESS_KEY_ID"] = "foo"
    if endpoint_url is None:
        endpoint_url = s3_test_server_endpoint()
    assert endpoint_url is not None
    s3filesystem = S3FileSystem(
        anon=False, client_kwargs={"endpoint_url": endpoint_url})
    s3filesystem.invalidate_cache()
    return s3filesystem


def build_s3_test_bucket(s3filesystem: S3FileSystem | None = None) -> str:
    """Create an s3 test buckent."""
    with tempfile.TemporaryDirectory("s3_test_bucket") as tmp_path:
        if s3filesystem is None:
            s3filesystem = build_s3_test_filesystem()
        bucket_url = f"s3:/{tmp_path}"
        s3filesystem.mkdir(bucket_url, acl="public-read")
        return bucket_url


@contextlib.contextmanager
def build_s3_test_protocol(
    root_path: pathlib.Path,
) -> Generator[FsspecReadWriteProtocol, None, None]:
    """Run an S3 moto server and construct fsspec genomic resource protocol.

    The S3 moto server is populated with resource from filesystem GRR pointed
    by the root_path.
    """
    endpoint_url = s3_test_server_endpoint()
    s3filesystem = build_s3_test_filesystem(endpoint_url)
    bucket_url = build_s3_test_bucket(s3filesystem)

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
        src_proto: FsspecReadOnlyProtocol) -> None:
    for res in src_proto.get_all_resources():
        dest_proto.copy_resource(res)
    dest_proto.build_content_file()
    dest_proto.filesystem.invalidate_cache()


@contextlib.contextmanager
def proto_builder(
    scheme: str, content: dict,
) -> Generator[
        FsspecReadOnlyProtocol | FsspecReadWriteProtocol,
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
