import os
import tempfile

import pyarrow as pa


class HdfsHelpers(object):

    def __init__(self, hdfs_host, hdfs_port):
        assert hdfs_host
        assert hdfs_port

        print("hdfs connecting to:", hdfs_host, hdfs_port)

        self.host = hdfs_host
        self.port = hdfs_port
        self.hdfs = pa.hdfs.connect(host=self.host, port=self.port)

    def exists(self, path):
        return self.hdfs.exists(path)

    def mkdir(self, path):
        print(path)
        self.hdfs.mkdir(path)
        self.chmod(path, 0o777)

    def tempdir(self, prefix='', suffix=''):
        dirname = tempfile.mktemp(prefix=prefix, suffix=suffix)
        self.mkdir(dirname)
        assert self.exists(dirname)

        return dirname

    def chmod(self, path, mode):
        return self.hdfs.chmod(path, mode)

    def delete(self, path, recursive=False):
        return self.hdfs.delete(path, recursive=recursive)

    def filesystem(self):
        return self.hdfs

    def put(self, local_filename, hdfs_filename):
        assert os.path.exists(local_filename)

        with open(local_filename, 'rb') as infile:
            self.hdfs.upload(hdfs_filename, infile)

    def put_in_directory(self, local_file, hdfs_dirname):
        basename = os.path.basename(local_file)
        hdfs_filename = os.path.join(hdfs_dirname, basename)

        self.put(local_file, hdfs_filename)

    def put_content(self, local_path, hdfs_dirname):
        assert os.path.exists(local_path)

        if os.path.is_dir(local_path):
            for local_file in os.listdir(local_path):
                self.put_in_directory(local_file, hdfs_dirname)
        else:
            self.put_in_directory(local_path, hdfs_dirname)

    def get(self, hdfs_filename, local_filename):
        # assert os.path.exists(local_filename)
        assert self.exists(hdfs_filename)

        with open(local_filename, "wb") as outfile:
            self.hdfs.download(hdfs_filename, outfile)

    def list_dir(self, hdfs_dirname):
        return self.hdfs.ls(hdfs_dirname)
