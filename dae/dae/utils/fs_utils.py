from fsspec.core import url_to_fs  # type: ignore


def exists(filename):
    fs, relative_path = url_to_fs(filename)
    return fs.exists(relative_path)
