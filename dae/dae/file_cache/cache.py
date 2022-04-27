"""File level resource cached"""
import os


class ResourceFileCache:
    """Provides file level resource cached"""

    def __init__(self, cache_dir, grr):
        self.cache_dir = cache_dir
        self.grr = grr

    def _save_resource_file(self, resource, file, cache_filepath, is_binary):
        read_mode = "rb" if is_binary else "r"
        os.makedirs(os.path.dirname(cache_filepath), exist_ok=True)
        write_mode = "wb" if is_binary else "w"
        with resource.open_raw_file(file, mode=read_mode) as infile, \
                open(cache_filepath, write_mode) as outfile:
            outfile.write(infile.read())

    def get_file_path(self, resource_id, filename, is_binary=False):
        """Given resource_id and filename returns local filesystem path
        to the resource file
        
        In case the specified filename does not belong to the resource
        raises a ValueError exception"""
        resource = self.grr.get_resource(resource_id)
        return self.get_file_path_from_resource(resource, filename, is_binary)

    def get_file_path_from_resource(self, resource, filename, is_binary=False):
        """Given resource and filename returns local filesystem path
        to the resource file
        
        In case the specified filename does not belong to the resource
        raises a ValueError exception"""

        if not resource.file_exists(filename):
            raise ValueError(
                f"resource {resource.resource_id} has no file {filename}")

        cache_filepath = os.path.join(
            self.cache_dir, resource.resource_id, filename)

        if not os.path.exists(cache_filepath):
            self._save_resource_file(
                resource, filename, cache_filepath, is_binary)
        return cache_filepath
