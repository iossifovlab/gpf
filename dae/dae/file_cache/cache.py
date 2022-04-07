import os


class ResourceFileCache:
    def __init__(self, cache_dir, grr=None):
        dae_db_dir = os.environ.get("DAE_DB_DIR")
        self.cache_dir = os.path.join(dae_db_dir, "file_cache", cache_dir)
        self.grr = grr

    def _save_resource_file(self, resource, file, save_filepath, is_binary):
        read_mode = "rb" if is_binary else "r"
        file = resource.open_raw_file(file, mode=read_mode)
        os.makedirs(os.path.dirname(save_filepath), exist_ok=True)
        write_mode = "wb" if is_binary else "w"
        with open(save_filepath, write_mode) as file_copy:
            file_copy.write(file.read())
        file.close()

    def get_file_path(self, resource_id, file, is_binary=False):
        assert self.grr is not None
        filepath = os.path.join(self.cache_dir, resource_id, file)
        if not os.path.exists(filepath):
            resource = self.grr.get_resource(resource_id)
            self._save_resource_file(resource, file, filepath, is_binary)
        return filepath

    def get_file_path_from_resource(self, resource, file, is_binary=False):
        filepath = os.path.join(self.cache_dir, resource.resource_id, file)
        if not os.path.exists(filepath):
            self._save_resource_file(resource, file, filepath, is_binary)
        return filepath
