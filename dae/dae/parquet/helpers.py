import logging
from urllib.parse import urlparse

import pyarrow as pa
import pyarrow.parquet as pq
from fsspec.core import url_to_fs
from pyarrow import fs as pafs

logger = logging.getLogger(__name__)


def url_to_pyarrow_fs(
    filename: str,
) -> tuple[pafs.FileSystem | None, str]:
    """Turn URL into pyarrow filesystem instance.

    Parameters
    ----------
    filename : str
        The fsspec-compatible URL

    Returns
    -------
    filesystem : pyarrow.fs.FileSystem
        The new filesystem discovered from ``filename`` and ``filesystem``.
    """

    if urlparse(filename).scheme:
        fsspec_fs, path = url_to_fs(filename)
        pa_fs = pafs.PyFileSystem(
            pafs.FSSpecHandler(fsspec_fs))  # type: ignore
        return pa_fs, path
    return None, filename


def merge_parquets(
    in_files: list[str], out_file: str,
    *,
    delete_in_files: bool = True,
    row_group_size: int = 50_000,
    parquet_version: str | None = None,
) -> None:
    """Merge `in_files` into one large file called `out_file`."""
    try:
        _try_merge_parquets(
            in_files, out_file,
            delete_in_files=delete_in_files,
            row_group_size=row_group_size,
            parqet_version=parquet_version)
    except Exception:  # pylint: disable=broad-except
        # unsuccessfull conversion. Remove the partially generated file.
        fs, path = url_to_fs(out_file)
        if fs.exists(path):
            fs.rm_file(path)
        raise


def _merge_flush_batches(
    batches: list[pa.RecordBatch],
    out_parquet: pq.ParquetWriter,
) -> None:
    if len(batches) == 0:
        return
    table = pa.Table.from_batches(batches)
    out_parquet.write_table(table)


def _collect_in_files_compression(
    in_files: list[str],
) -> str | dict[str, str]:
    compression: str | dict[str, str] = "SNAPPY"
    if len(in_files) > 0:
        for in_file in in_files:
            fs, path = url_to_fs(in_file)
            if not fs.exists(path):
                continue

            parq_file = pq.ParquetFile(path)
            if parq_file.metadata.num_row_groups == 0:
                continue

            compression = {}
            row_group = parq_file.metadata.row_group(0)
            schema = parq_file.schema_arrow

            for name in schema.names:
                for index in range(row_group.num_columns):
                    column = row_group.column(index)
                    if column.path_in_schema != name:
                        continue
                    column_compression = column.compression
                    if column_compression.upper() == "UNCOMPRESSED":
                        continue
                    compression[name] = column_compression
    return compression


def _try_merge_parquets(
    in_files: list[str], out_file: str,
    *,
    delete_in_files: bool,
    row_group_size: int = 50_000,
    parqet_version: str | None = None,
) -> None:
    assert len(in_files) > 0
    out_parquet = None

    compression = _collect_in_files_compression(in_files)

    batches = []
    batches_row_count = 0
    parq_file = None

    for in_file in in_files:
        in_fs, in_fn = url_to_pyarrow_fs(in_file)
        if in_fs is None:
            in_fs = pafs.LocalFileSystem()
        try:
            with in_fs.open_input_file(in_fn) as parquet_native_file:
                parq_file = pq.ParquetFile(parquet_native_file)
                if out_parquet is None:
                    out_filesystem, out_filename = url_to_pyarrow_fs(out_file)
                    out_parquet = pq.ParquetWriter(
                        out_filename, parq_file.schema_arrow,
                        filesystem=out_filesystem,
                        compression=compression,  # type: ignore
                        version=parqet_version,  # type: ignore
                    )
                for batch in parq_file.iter_batches():
                    batches.append(batch)
                    batches_row_count += batch.num_rows
                    if batches_row_count >= row_group_size:
                        _merge_flush_batches(batches, out_parquet)
                        batches = []
                        batches_row_count = 0

        except pa.ArrowInvalid:
            logger.exception(
                "invalid chunk parquet file: %s", in_file)
            raise
        except FileNotFoundError:
            logger.warning(
                "missing chunk parquet file: %s", in_file)

    if len(batches) > 0:
        assert parq_file is not None
        if out_parquet is None:
            out_filesystem, out_filename = url_to_pyarrow_fs(out_file)
            out_parquet = pq.ParquetWriter(
                out_filename, parq_file.schema_arrow,
                filesystem=out_filesystem,
                compression=compression,  # type: ignore
                version=parqet_version,  # type: ignore
            )
        table = pa.Table.from_batches(batches)
        out_parquet.write_table(table)

    batches = []
    batches_row_count = 0

    if out_parquet is not None:
        out_parquet.close()

    if delete_in_files:
        for in_file in in_files:
            try:
                fs, path = url_to_fs(in_file)
                fs.rm_file(path)
            except FileNotFoundError:
                logger.warning("missing chunk parquet file: %s", in_file)
