from box import Box  # type: ignore

from dae.backends.storage.impala_genotype_storage import ImpalaGenotypeStorage
from dae.backends.storage.schema2_genotype_storage import (
    Schema2GenotypeStorage
)
from dae.backends.storage.filesystem_genotype_storage import (
    FilesystemGenotypeStorage,
)


class GenotypeStorageFactory:
    """Create the correct Genotype Storage."""

    def __init__(self, dae_config):
        self.storage_config = dae_config.storage
        self.default_storage_id = dae_config.genotype_storage.default

        if self.storage_config is None:
            default_config = {
                "genotype_filesystem": {
                    "dir": f"{dae_config.conf_dir}/studies",
                    "storage_type": "filesystem",
                }
            }
            self.storage_config = Box(default_config)

        self._genotype_storage_cache = {}

    def get_default_genotype_storage(self):
        return self.get_genotype_storage(self.default_storage_id)

    def get_genotype_storage(self, genotype_storage_id):
        """Create and return a genotype storage with id genotype_storage_id."""
        if genotype_storage_id is None:
            return self.get_default_genotype_storage()

        self._load_genotype_storage({genotype_storage_id})

        if genotype_storage_id not in self._genotype_storage_cache:
            return None

        return self._genotype_storage_cache[genotype_storage_id]

    def get_genotype_storage_ids(self):
        return list(self.storage_config.keys())

    def _load_genotype_storage(self, genotype_storage_ids=None):
        if genotype_storage_ids is None:
            genotype_storage_ids = set(self.get_genotype_storage_ids())

        assert isinstance(genotype_storage_ids, set)

        cached_ids = set(self._genotype_storage_cache.keys())
        if genotype_storage_ids != cached_ids:
            to_load = genotype_storage_ids - cached_ids
            for genotype_storage_id in to_load:
                self._load_genotype_storage_in_cache(genotype_storage_id)

    def _load_genotype_storage_in_cache(self, genotype_storage_id):
        conf = self.storage_config.get(genotype_storage_id, None)
        if not conf:
            return

        genotype_storage = None
        if conf.storage_type == "impala":
            if conf.schema_version == 1:
                genotype_storage = ImpalaGenotypeStorage(
                    conf, genotype_storage_id)
            else:
                assert conf.schema_version == 2
                genotype_storage = Schema2GenotypeStorage(
                    conf, genotype_storage_id)
        elif conf.storage_type == "filesystem":
            genotype_storage = FilesystemGenotypeStorage(
                conf, genotype_storage_id)

        assert genotype_storage

        self._genotype_storage_cache[genotype_storage_id] = genotype_storage
