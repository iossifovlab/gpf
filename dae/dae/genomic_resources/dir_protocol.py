import pathlib
import gzip

from typing import List, Generator

from dae.genomic_resources.repository import ReadWriteRepositoryProtocol, \
    ManifestEntry, \
    GenomicResource, \
    find_genomic_resources_helper, \
    find_genomic_resource_files_helper


class DirectoryProtocol(ReadWriteRepositoryProtocol):
    """Provides filesystem genomic resources repository protocol."""

    def __init__(self, proto_id: str, directory, **kwargs):
        super().__init__(proto_id)
        self.directory: pathlib.Path = pathlib.Path(directory)
        self.directory.mkdir(exist_ok=True, parents=True)

    @staticmethod
    def _path_to_dict(directory: pathlib.Path):
        if not directory.exists():
            return {}
        if directory.is_dir():
            result = {}
            for entry in directory.iterdir():
                if entry.name in {".", ".."}:
                    continue
                if entry.name.startswith("."):
                    continue
                result[entry.name] = DirectoryProtocol._path_to_dict(entry)
            return result

        return directory

    def collect_all_resources(self) -> Generator[GenomicResource, None, None]:
        """Returns generator for all resources managed by this protocol."""
        dir_content = self._path_to_dict(self.directory)
        for res_id, res_ver in find_genomic_resources_helper(dir_content):
            yield self.build_genomic_resource(res_id, res_ver)

    def get_resource_path(self, resource) -> pathlib.Path:
        """Returns directory pathlib.Path for specified resources."""
        return self.directory.joinpath(
            resource.get_genomic_resource_id_version())

    def get_resource_file_path(self, resource, filename: str) -> pathlib.Path:
        """Returns pathlib.Path for a file in a resource."""
        return self.get_resource_path(resource).joinpath(filename)

    def collect_resource_entries(self, resource) -> List[ManifestEntry]:
        """Returns a list of tuples for all files in a resources."""
        content_dict = self._path_to_dict(
            self.get_resource_path(resource))

        def my_leaf_to_size_and_time(filepath):
            filestat = filepath.stat()
            filetime = ManifestEntry.convert_timestamp(filestat.st_mtime)
            return filestat.st_size, filetime

        result = []
        for fname, fsize, ftime in find_genomic_resource_files_helper(
                content_dict, my_leaf_to_size_and_time):
            result.append(ManifestEntry(fname, fsize, ftime, None))
        return result

    def open_raw_file(self, resource: GenomicResource, filename: str,
                      mode="rt", uncompress=False, _seekable=False):

        filepath = self.get_resource_file_path(resource, filename)
        if "w" in mode:
            # Create the containing directory if it doesn't exists.
            # This align DireRepo API with URL and fspec APIs
            filepath.mkdir(exist_ok=True)

        if filename.endswith(".gz") and uncompress:
            if "w" in mode:
                raise IOError("writing gzip files not supported")
            return gzip.open(filepath.open(mode="rb"), mode)

        return filepath.open(mode=mode)  # pylint: disable=unspecified-encoding
