import logging

from typing import cast, Optional, Union
from urllib.parse import urlparse
from fsspec.spec import AbstractFileSystem
from fsspec.core import url_to_fs
import pyarrow as pa
import pyarrow.parquet as pq


logger = logging.getLogger(__name__)


def url_to_pyarrow_fs(
        filename: str,
        filesystem: Optional[AbstractFileSystem] = None) -> pa.fs.FileSystem:
    """Turn URL into pyarrow filesystem instance.

    Parameters
    ----------
    filename : str
        The fsspec-compatible URL
    filesystem : fsspec.FileSystem
        An fsspec filesystem for ``filename``.

    Returns
    -------
    filesystem : pyarrow.fs.FileSystem
        The new filesystem discovered from ``filename`` and ``filesystem``.
    """
    if isinstance(filesystem, pa.fs.FileSystem):
        return filesystem, filename

    if filesystem is None:
        if urlparse(filename).scheme:
            fsspec_fs, path = url_to_fs(filename)
            pa_fs = pa.fs.PyFileSystem(pa.fs.FSSpecHandler(fsspec_fs))
            return pa_fs, path
        return None, filename

    pa_fs = pa.fs.PyFileSystem(pa.fs.FSSpecHandler(filesystem))
    return pa_fs, filename


def merge_parquets(
    in_files: list[str], out_file: str,
    delete_in_files: bool = True,
    row_group_size: int = 50_000,
    parquet_version: Optional[str] = None
) -> None:
    """Merge `in_files` into one large file called `out_file`."""
    try:
        _try_merge_parquets(
            in_files, out_file, delete_in_files,
            row_group_size, parquet_version)
    except Exception:  # pylint: disable=broad-except
        # unsuccessfull conversion. Remove the partially generated file.
        fs, path = url_to_fs(out_file)
        if fs.exists(path):
            fs.rm_file(path)
        raise


def _merge_flush_batches(
    batches: list[pa.RecordBatch],
    out_parquet: pq.ParquetWriter
) -> None:
    if len(batches) == 0:
        return
    table = pa.Table.from_batches(batches)
    out_parquet.write_table(table)


def _try_merge_parquets(
    in_files: list[str], out_file: str, delete_in_files: bool,
    row_group_size: int = 50_000,
    parqet_version: Optional[str] = None
) -> None:
    assert len(in_files) > 0
    out_parquet = None

    compression: Union[str, dict[str, str]] = "SNAPPY"
    if len(in_files) > 0:
        fs, path = url_to_fs(in_files[0])
        if fs.exists(path):
            compression = {}
            parq_file = pq.ParquetFile(path)
            row_group = parq_file.metadata.row_group(0)
            schema = parq_file.schema_arrow
            for index, name in enumerate(schema.names):
                column_compression = row_group.column(index).compression
                if column_compression.upper() == "UNCOMPRESSED":
                    continue
                compression[name] = column_compression

    batches = []
    batches_row_count = 0
    for in_file in in_files:
        in_fs, in_fn = url_to_pyarrow_fs(in_file)
        if in_fs is None:
            in_fs = pa.fs.LocalFileSystem()
        try:
            with in_fs.open_input_file(in_fn) as parquet_native_file:
                parq_file = pq.ParquetFile(parquet_native_file)
                if out_parquet is None:
                    out_filesystem, out_filename = url_to_pyarrow_fs(out_file)
                    out_parquet = pq.ParquetWriter(
                        out_filename, parq_file.schema_arrow,
                        filesystem=out_filesystem,
                        compression=compression,
                        version=parqet_version
                    )
                for batch in parq_file.iter_batches():
                    batches.append(batch)
                    batches_row_count += batch.num_rows
                    if batches_row_count >= row_group_size:
                        _merge_flush_batches(batches, out_parquet)
                        batches = []
                        batches_row_count = 0

        except pa.ArrowInvalid:
            logger.error(
                "invalid chunk parquet file: %s", in_file, exc_info=True)
            raise
        except FileNotFoundError:
            logger.warning(
                "missing chunk parquet file: %s", in_file)

    _merge_flush_batches(batches, out_parquet)
    batches = []
    batches_row_count = 0

    cast(pq.ParquetWriter, out_parquet).close()

    if delete_in_files:
        for in_file in in_files:
            try:
                fs, path = url_to_fs(in_file)
                fs.rm_file(path)
            except FileNotFoundError:
                logger.warning("missing chunk parquet file: %s", in_file)
