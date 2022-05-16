import os
import re
import tempfile
import logging

from pyarrow import fs  # type: ignore
from fsspec.implementations.arrow import ArrowFSWrapper  # type: ignore


logger = logging.getLogger(__name__)


class HdfsHelpers:
    def __init__(self, hdfs_host, hdfs_port, replication=None):
        assert hdfs_host
        assert hdfs_port

        if os.environ.get("DAE_HDFS_HOST", None) is not None:
            hdfs_host = os.environ.get("DAE_HDFS_HOST")
            print("hdfs overwrite connecting to:", hdfs_host, hdfs_port)

        self.host = hdfs_host
        self.port = hdfs_port
        self.replication = replication
        self._hdfs = None

    @property
    def hdfs(self):
        if self._hdfs is None:
            extra_conf = None
            if self.replication and self.replication > 0:
                assert self.replication > 0, self.replication
                extra_conf = {
                    "dfs.replication": str(self.replication)
                }
            logger.info(
                f"hdfs connecting to: {self.host}:{self.port}; "
                f"extra: {extra_conf}")
            hdfs = fs.HadoopFileSystem(
                host=self.host, port=self.port, extra_conf=extra_conf)
            self._hdfs = ArrowFSWrapper(hdfs)
        return self._hdfs

    def exists(self, path):
        return self.hdfs.exists(path)

    def mkdir(self, path):
        self.hdfs.mkdir(path)

    def makedirs(self, path):
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

    def tempdir(self, prefix="", suffix=""):
        dirname = tempfile.mktemp(prefix=prefix, suffix=suffix)  # NOSONAR
        logger.debug("creating temporary directory %s", dirname)
        self.mkdir(dirname)
        assert self.exists(dirname)

        return dirname

    def delete(self, path, recursive=False):
        return self.hdfs.delete(path, recursive=recursive)

    def filesystem(self):
        return self.hdfs

    def rename(self, path, new_path):
        self.hdfs.rename(path, new_path)

    def put(self, local_filename, hdfs_filename):
        assert os.path.exists(local_filename)

        self.hdfs.upload(local_filename, hdfs_filename)

    def put_in_directory(self, local_file, hdfs_dirname):
        basename = os.path.basename(local_file)
        hdfs_filename = os.path.join(hdfs_dirname, basename)

        self.put(local_file, hdfs_filename)

    def put_content(self, local_path, hdfs_dirname):
        assert os.path.exists(local_path), local_path

        if os.path.isdir(local_path):
            for local_file in os.listdir(local_path):
                self.put_in_directory(
                    os.path.join(local_path, local_file), hdfs_dirname
                )
        else:
            self.put_in_directory(local_path, hdfs_dirname)

    def get(self, hdfs_filename, local_filename):
        assert self.exists(hdfs_filename)

        with open(local_filename, "wb") as outfile:
            self.hdfs.download(hdfs_filename, outfile)

    def list_dir(self, hdfs_dirname):
        return self.hdfs.ls(hdfs_dirname)

    def isdir(self, hdfs_dirname):
        if not self.exists(hdfs_dirname):
            return False
        info = self.hdfs.info(hdfs_dirname)
        return info["type"] == "directory"

    def isfile(self, hdfs_filename):
        if not self.exists(hdfs_filename):
            return False
        info = self.hdfs.info(hdfs_filename)
        return info["type"] == "file"

    def list_parquet_files(self, hdfs_dirname, regexp=r".*\.parquet"):
        regexp = re.compile(regexp)

        def list_parquet_files_recursive(dirname, collection):
            assert self.isdir(dirname)
            allfiles = self.list_dir(dirname)
            for hfile in allfiles:
                if self.isdir(hfile):
                    list_parquet_files_recursive(hfile, collection)
                elif self.isfile(hfile) and regexp.match(hfile) and \
                        hfile not in collection:
                    collection.append(hfile)

        assert self.isdir(hdfs_dirname), hdfs_dirname

        result = []
        list_parquet_files_recursive(hdfs_dirname, result)
        return result
