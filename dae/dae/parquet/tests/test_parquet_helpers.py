import pyarrow as pa
from dae.parquet.helpers import url_to_pyarrow_fs


def test_url_to_pyarrow_fs():
    filename = "path/to/some/file.txt"
    fs, path = url_to_pyarrow_fs(filename)
    assert fs is None
    assert path == filename


def test_url_to_pyarrow_fs_s3_url():
    filename = "s3://bucket/file.txt"
    fs, path = url_to_pyarrow_fs(filename)
    assert isinstance(fs, pa.fs.PyFileSystem)
    assert path == "bucket/file.txt"
