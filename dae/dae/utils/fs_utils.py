from fsspec.core import url_to_fs  # type: ignore
import os
from urllib.parse import urlparse


def exists(filename):
    fs, relative_path = url_to_fs(filename)
    return fs.exists(relative_path)


def join(path, *paths):
    for i in range(len(paths)-1, -1, -1):
        if urlparse(paths[i]).scheme:
            return os.path.join(*paths[i:])
    return os.path.join(path, *paths)
