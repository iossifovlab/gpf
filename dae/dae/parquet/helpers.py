from typing import Any
from urllib.parse import urlparse
from fsspec.core import url_to_fs
import pyarrow as pa


def url_to_pyarrow_fs(filename: str, filesystem: Any = None):
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
