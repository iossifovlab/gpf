from dae.backends.storage.impala_genotype_storage import ImpalaGenotypeStorage
from dae.backends.storage.filesystem_genotype_storage import (
    FilesystemGenotypeStorage,
)


class GenotypeStorageFactory:
    def __init__(self, dae_config):
        self.dae_config = dae_config

        self._genotype_storage_cache = {}

    def get_default_genotype_storage(self):
        default_genotype_storage_id = self.dae_config.genotype_storage.default
        return self.get_genotype_storage(default_genotype_storage_id)

    def get_genotype_storage(self, genotype_storage_id):
        self._load_genotype_storage({genotype_storage_id})

        if genotype_storage_id not in self._genotype_storage_cache:
            return None

        return self._genotype_storage_cache[genotype_storage_id]

    def get_genotype_storage_ids(self):
        return list(getattr(self.dae_config, "storage")._fields)

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
        conf = getattr(self.dae_config.storage, genotype_storage_id, None)
        if not conf:
            return

        genotype_storage = None
        if conf.storage_type == "impala":
            genotype_storage = ImpalaGenotypeStorage(conf)
        elif conf.storage_type == "filesystem":
            genotype_storage = FilesystemGenotypeStorage(conf)

        assert genotype_storage

        self._genotype_storage_cache[genotype_storage_id] = genotype_storage
