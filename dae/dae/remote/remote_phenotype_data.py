from dae.pheno.pheno_db import PhenotypeData


class RemotePhenotypeData(PhenotypeData):
    def __init__(self, dataset_id, rest_client):
        self.dataset_id = dataset_id
        self.rest_client = rest_client

    def get_persons_df(self, roles, person_ids, family_ids):
        raise NotImplementedError()

    def get_persons_values_df(
        self, measure_ids, person_ids, family_ids, roles
    ):
        raise NotImplementedError()

    def get_persons(self, roles, person_ids, family_ids):
        raise NotImplementedError()

    def has_measure(self, measure_id):
        raise NotImplementedError()

    def get_measure(self, measure_id):
        raise NotImplementedError()

    def get_measures(self, instrument, measure_type):
        raise NotImplementedError()

    def get_measure_values_df(self, measure_id, person_ids, family_ids, roles):
        raise NotImplementedError()

    def get_measure_values(self, measure_id, person_ids, family_ids, roles):
        raise NotImplementedError()

    def get_values_df(self, measure_ids, person_ids, family_ids, roles):
        raise NotImplementedError()

    def get_values(self, measure_ids, person_ids, family_ids, roles):
        raise NotImplementedError()

    def get_instrument_values_df(
        self, instrument_id, person_ids, family_ids, roles
    ):
        raise NotImplementedError()

    def get_instrument_values(
        self, instrument_id, person_ids, family_ids, roles
    ):
        raise NotImplementedError()

    @property
    def instruments(self):
        raise NotImplementedError()
