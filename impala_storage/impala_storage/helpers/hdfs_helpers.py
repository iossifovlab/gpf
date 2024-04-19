import logging
import os
import tempfile
from typing import Optional, cast

from fsspec.implementations.arrow import ArrowFSWrapper
from pyarrow import fs

logger = logging.getLogger(__name__)


class HdfsHelpers:
    """Helper methods for working with HDFS."""

    def __init__(
        self, hdfs_host: str,
        hdfs_port: int,
        replication: Optional[int] = None,
    ) -> None:
        assert hdfs_host
        assert hdfs_port

        if os.environ.get("DAE_HDFS_HOST", None) is not None:
            hdfs_host = cast(str, os.environ.get("DAE_HDFS_HOST"))
            print("hdfs overwrite connecting to:", hdfs_host, hdfs_port)

        self.host = hdfs_host
        self.port = hdfs_port
        self.replication = replication
        self._hdfs = None

    @property
    def hdfs(self) -> ArrowFSWrapper:
        """Return a file system for working with HDFS."""
        if self._hdfs is None:
            extra_conf = None
            if self.replication and self.replication > 0:
                assert self.replication > 0, self.replication
                extra_conf = {
                    "dfs.replication": str(self.replication),
                }
            logger.info("hdfs connecting to: %s:%s; extra: %s",
                        self.host, self.port, extra_conf)
            hdfs = fs.HadoopFileSystem(
                host=self.host, port=self.port, extra_conf=extra_conf)
            self._hdfs = ArrowFSWrapper(hdfs)
        return self._hdfs

    def close(self) -> None:
        if self._hdfs is not None:
            del self._hdfs
        self._hdfs = None

    def exists(self, path: str) -> bool:
        return cast(bool, self.hdfs.exists(path))

    def mkdir(self, path: str) -> None:
        self.hdfs.mkdir(path)

    def makedirs(self, path: str) -> bool:
        """Make all directories along the path."""
        if path[0] == os.sep:
            paths = path[1:].split(os.sep)
            paths[0] = "/" + paths[0]
        else:
            paths = path.split(os.sep)
        current_path = ""
        for directory in paths:
            current_path = os.path.join(current_path, directory)
            if not self.exists(current_path):
                self.mkdir(current_path)

        return self.exists(current_path)

    def tempdir(self, prefix: str = "", suffix: str = "") -> str:
        dirname = tempfile.mktemp(prefix=prefix, suffix=suffix)
        logger.debug("creating temporary directory %s", dirname)
        self.mkdir(dirname)
        assert self.exists(dirname)

        return dirname

    def delete(self, path: str, recursive: bool = False) -> None:
        self.hdfs.delete(path, recursive=recursive)

    def filesystem(self) -> ArrowFSWrapper:
        return self.hdfs

    def rename(self, path: str, new_path: str) -> None:
        self.hdfs.rename(path, new_path)

    def put(
        self, local_filename: str,
        hdfs_filename: str,
        recursive: bool = False,
    ) -> None:
        """Copy a file or directory from the local filesystem to HDFS.

        Args:
            local_filename (str): The path of the local file or directory
                to be copied.
            hdfs_filename (str): The destination path in HDFS.
            recursive (bool, optional): Whether to copy directories
                recursively. Defaults to False.

        Raises:
            AssertionError: If the local file does not exist.
        """
        assert os.path.exists(local_filename), local_filename

        self.hdfs.put(local_filename, hdfs_filename, recursive=recursive)

    def put_in_directory(self, local_file: str, hdfs_dirname: str) -> None:
        basename = os.path.basename(local_file)
        hdfs_filename = os.path.join(hdfs_dirname, basename)

        self.put(local_file, hdfs_filename)

    def put_content(self, local_path: str, hdfs_dirname: str) -> None:
        """Copy local_path to hdfs_dirname."""
        assert os.path.exists(local_path), local_path

        if os.path.isdir(local_path):
            for local_file in os.listdir(local_path):
                self.put_in_directory(
                    os.path.join(local_path, local_file), hdfs_dirname,
                )
        else:
            self.put_in_directory(local_path, hdfs_dirname)

    def get(self, hdfs_filename: str, local_filename: str) -> None:
        assert self.exists(hdfs_filename)

        with open(local_filename, "wb") as outfile:
            self.hdfs.download(hdfs_filename, outfile)

    # def list_dir(self, hdfs_dirname: str) -> list[str]:
    #     return cast(list[str], self.hdfs.ls(hdfs_dirname))

    def isdir(self, hdfs_dirname: str) -> bool:
        if not self.exists(hdfs_dirname):
            return False
        info = self.hdfs.info(hdfs_dirname)
        return bool(info["type"] == "directory")

    def isfile(self, hdfs_filename: str) -> bool:
        if not self.exists(hdfs_filename):
            return False
        info = self.hdfs.info(hdfs_filename)
        return bool(info["type"] == "file")

    # def list_parquet_files(
    #     self, hdfs_dirname: str,
    #     regexp: str = r".*\.parquet"
    # ) -> list[str]:
    #     """List all parquet files in hdfs_dirname."""
    #     regexp = re.compile(regexp)

    #     def list_parquet_files_recursive(dirname, collection):
    #         assert self.isdir(dirname)
    #         allfiles = self.list_dir(dirname)
    #         for hfile in allfiles:
    #             if self.isdir(hfile):
    #                 list_parquet_files_recursive(hfile, collection)
    #             elif self.isfile(hfile) and regexp.match(hfile) and \
    #                     hfile not in collection:
    #                 collection.append(hfile)

    #     assert self.isdir(hdfs_dirname), hdfs_dirname

    #     result: list[str] = []
    #     list_parquet_files_recursive(hdfs_dirname, result)
    #     return result
