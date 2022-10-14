import os
from pathlib import Path
from urllib.parse import urlparse
from typing import Optional, Union

from fsspec.core import url_to_fs


def exists(filename):
    fs, relative_path = url_to_fs(filename)
    return fs.exists(relative_path)


def join(path, *paths):
    for i in range(len(paths) - 1, -1, -1):
        if urlparse(paths[i]).scheme:
            return os.path.join(*paths[i:])
    return os.path.join(path, *paths)


def find_directory_with_a_file(
        filename: str,
        cwd: Optional[Union[str, Path]] = None) -> Optional[Path]:
    """Find a directory containing a file.

    Starts from current working directory or from a directory passed.
    """
    if cwd is None:
        curr_dir = Path().absolute()
    else:
        curr_dir = Path(cwd).absolute()

    pathname = curr_dir / filename
    if pathname.exists():
        return curr_dir

    for work_dir in curr_dir.parents:
        pathname = work_dir / filename
        if pathname.exists():
            return work_dir

    return None
