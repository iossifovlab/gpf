import os

class GenotypeStorage:

    def __init__(self, storage_config):
        self.storage_config = storage_config

    def _get_data_path(self, study_id):
        return os.path.abspath(
            os.path.join(self.storage_config.dir, study_id, 'data')
        )

    def get_backend(self, study_config, genomes_db):
        raise NotImplementedError()
