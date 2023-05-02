import datetime
import os
import shutil
from pathlib import Path
from urllib.parse import urlparse
from typing import Optional, Union, cast

from fsspec.core import url_to_fs


def abspath(filename):
    url = urlparse(filename)
    if url.scheme:
        return filename
    return os.path.abspath(filename)


def exists(filename):
    fs, relative_path = url_to_fs(filename)
    return fs.exists(relative_path)


def join(path, *paths) -> str:
    for i in range(len(paths) - 1, -1, -1):
        if urlparse(paths[i]).scheme:
            return str(os.path.join(*paths[i:]))
    return str(os.path.join(path, *paths))


def find_directory_with_a_file(
        filename: str,
        cwd: Optional[Union[str, Path]] = None) -> Optional[Path]:
    """Find a directory containing a file.

    Starts from current working directory or from a directory passed.
    """
    if cwd is None:
        curr_dir = Path(os.getcwd()).absolute()
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


def modified(filename: str) -> datetime.datetime:
    """Return the modified timestamp of a file."""
    fs, relative_path = url_to_fs(filename)
    return cast(datetime.datetime, fs.modified(relative_path))


def containing_path(path: Union[str, os.PathLike]) -> str:
    """Return url to the resource that contains path.

    For file paths this is equivalent to the containing directory.
    For urls this is equivalent to the containing resource.
    """
    if not path:
        return str(path)
    url = urlparse(str(path))
    if url.scheme:
        if url.path:
            return os.path.dirname(path)
        return url.scheme + "://"
    return os.path.dirname(os.path.realpath(path))


def sign(filename: str) -> str:
    """Create a signed URL representing the given path.

    If the coresponding filesystem doesn't support signing then the filename
    is returned as is.
    """
    fs, relative_path = url_to_fs(filename)
    try:
        return cast(str, fs.sign(relative_path))
    except NotImplementedError:
        return filename


def copy(dest: str, src: str) -> None:
    shutil.copytree(src, dest, dirs_exist_ok=True)


def tabix_index_filename(tabix_filename: str) -> Optional[str]:
    """Given a Tabix/VCF filename returns a tabix index filename if exists."""
    if not exists(tabix_filename):
        raise IOError(f"tabix file '{tabix_filename}' not found")

    tbi_index_filename = f"{tabix_filename}.tbi"
    if exists(tbi_index_filename):
        return tbi_index_filename

    csi_index_filename = f"{tabix_filename}.csi"
    if exists(csi_index_filename):
        return csi_index_filename

    return None


def glob(path: str) -> list[str]:
    """Find files by glob-matching."""
    fs, relative_path = url_to_fs(path)
    return cast(list[str], fs.glob(relative_path))


def rm_file(path: str):
    """Remove a file."""
    fs, relative_path = url_to_fs(path)
    return fs.rm_file(relative_path)


def _handle_env_variables(envdict=None):
    """Handle filesystem-related environment variables.

    Passing certain settings as env variables is useful in certain scenarios
    like running on k8s. However certain fsspec settings canNOT be
    passed as env vars - see:
     * https://github.com/fsspec/s3fs/issues/432
     * https://github.com/fsspec/filesystem_spec/issues/1130

    To work around this issue we have our own set of environment variables. On
    module import we get these env variables and set the appropriate config
    variables for fsspec.
    """
    envdict = envdict if envdict is not None else os.environ
    if "S3_ENDPOINT_URL" not in envdict:
        return
    endpoint_url = envdict["S3_ENDPOINT_URL"]

    from fsspec.config import conf  # pylint: disable=import-outside-toplevel
    conf["s3"] = conf.get("s3", {})
    conf["s3"]["client_kwargs"] = conf["s3"].get("client_kwargs", {})
    client_kwargs = conf["s3"]["client_kwargs"]
    if "endpoint_url" not in client_kwargs:
        client_kwargs["endpoint_url"] = endpoint_url


_handle_env_variables()
