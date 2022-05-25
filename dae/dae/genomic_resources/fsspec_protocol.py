from bz2 import compress
import pathlib
import gzip

from typing import List, Generator, cast

import pysam

from dae.genomic_resources.repository import ReadWriteRepositoryProtocol, \
    ManifestEntry, \
    GenomicResource, \
    find_genomic_resources_helper, \
    find_genomic_resource_files_helper


class FsspecReadWriteProtocol(ReadWriteRepositoryProtocol):
    """Provides filesystem genomic resources repository protocol."""

    def __init__(self, proto_id: str, root_url, filesystem, **kwargs):
        super().__init__(proto_id)
        self.root_url = pathlib.Path(root_url)
        self.filesystem = filesystem
        self.filesystem.makedirs(self.root_url, exist_ok=True)

    def _path_to_dict(self, parent: pathlib.Path):

        if not self.filesystem.exists(parent):
            return {}
        elif self.filesystem.isdir(parent):
            result = {}
            for entry in self.filesystem.ls(parent, detail=True):
                path = pathlib.Path(entry["name"]).relative_to(self.root_url)
                if path.name in {".", ".."}:
                    continue
                if path.name.startswith("."):
                    continue
                result[path.name] = self._path_to_dict(entry["name"])
            return result

        return parent

    def collect_all_resources(self) -> Generator[GenomicResource, None, None]:
        """Returns generator for all resources managed by this protocol."""
        dir_content = self._path_to_dict(self.root_url)
        for res_id, res_ver in find_genomic_resources_helper(dir_content):
            yield self.build_genomic_resource(res_id, res_ver)

    def get_resource_path(self, resource) -> pathlib.Path:
        """Returns directory pathlib.Path for specified resources."""
        return self.root_url.joinpath(
            resource.get_genomic_resource_id_version())

    def get_resource_file_path(self, resource, filename: str) -> pathlib.Path:
        """Returns pathlib.Path for a file in a resource."""
        return self.get_resource_path(resource).joinpath(filename)

    def collect_resource_entries(self, resource) -> List[ManifestEntry]:
        """Returns a list of tuples for all files in a resources."""
        content_dict = self._path_to_dict(
            self.get_resource_path(resource))

        def my_leaf_to_size_and_time(filepath):
            fileinfo = self.filesystem.info(filepath)
            filetime = ManifestEntry.convert_timestamp(fileinfo["mtime"])
            return fileinfo["size"], filetime

        result = []
        for fname, fsize, ftime in find_genomic_resource_files_helper(
                content_dict, my_leaf_to_size_and_time):
            result.append(ManifestEntry(fname, fsize, ftime, None))
        return sorted(result)

    def file_exists(self, resource, filename) -> bool:
        filepath = self.get_resource_file_path(resource, filename)
        return cast(bool, self.filesystem.exists(filepath))

    def open_raw_file(self, resource: GenomicResource, filename: str,
                      mode="rt", **kwargs):

        filepath = self.get_resource_file_path(resource, filename)
        if "w" in mode:
            # Create the containing directory if it doesn't exists.
            if not self.filesystem.exists(filepath.parent):
                self.filesystem.mkdir(
                    filepath.parent, create_parents=True, exist_ok=True)

        compression = None
        if kwargs.get("compression"):
            compression="gzip"
        return self.filesystem.open(
            filepath, mode=mode, compression=compression)  # pylint: disable=unspecified-encoding

    def open_tabix_file(self, resource,  filename,
                        index_filename=None):
        file_path = str(self.get_resource_file_path(resource, filename))
        index_path = None
        if index_filename:
            index_path = str(self.get_resource_file_path(
                resource, index_filename))
        return pysam.TabixFile(file_path, index=index_path)  # pylint: disable=no-member
