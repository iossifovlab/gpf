import pandas as pd
from collections import OrderedDict
from dae.pheno.pheno_db import PhenotypeData, Measure, Instrument
from dae.pedigrees.family import Person


class RemotePhenotypeData(PhenotypeData):
    def __init__(self, dataset_id, rest_client):
        self.dataset_id = dataset_id
        self.rest_client = rest_client
        self._instruments = None

    def get_persons_df(self, roles=None, person_ids=None, family_ids=None):
        persons = self.rest_client.post_pheno_persons(
            self.dataset_id,
            roles,
            person_ids,
            family_ids
        )

        return pd.DataFrame.from_records(persons.values())

    def get_persons_values_df(
        self, measure_ids, person_ids=None, family_ids=None, roles=None
    ):
        persons = self.rest_client.post_pheno_persons_values(
            self.dataset_id,
            roles,
            person_ids,
            family_ids
        )

        return pd.DataFrame.from_records(persons.values())

    def get_persons(self, roles=None, person_ids=None, family_ids=None):
        persons = self.rest_client.post_pheno_persons(
            self.dataset_id,
            roles,
            person_ids,
            family_ids
        )
        for k, v in persons.items():
            persons[k] = Person(**v)

        return persons

    def has_measure(self, measure_id):
        measure = self.rest_client.get_measure(self.dataset_id, measure_id)

        return measure is not None

    def get_measure(self, measure_id):
        measure = self.rest_client.get_measure(self.dataset_id, measure_id)

        return Measure.from_json(measure)

    def get_measures(self, instrument=None, measure_type=None):
        measures = self.rest_client.get_measures(
            self.dataset_id,
            instrument,
            measure_type
        )
        return {m["measureName"]: Measure.from_json(m) for m in measures}

    def get_measure_values_df(
        self,
        measure_id,
        person_ids=None,
        family_ids=None,
        roles=None,
        default_filter="apply",
    ):
        measure_values = self.rest_client.post_measure_values(
            self.dataset_id,
            measure_id,
            person_ids,
            family_ids,
            roles,
            default_filter
        )
        data = {
            "person_id": measure_values.keys(),
            measure_id: measure_values.values()
        }

        return pd.DataFrame(data)

    def get_measure_values(
        self,
        measure_id,
        person_ids=None,
        family_ids=None,
        roles=None,
        default_filter="apply",
    ):
        measure_values = self.rest_client.post_measure_values(
            self.dataset_id,
            measure_id,
            person_ids,
            family_ids,
            roles,
            default_filter
        )

        return measure_values

    def get_values_df(
        self,
        measure_ids,
        person_ids=None,
        family_ids=None,
        roles=None,
        default_filter="apply",
    ):
        values = self.rest_client.post_measure_values(
            self.dataset_id,
            measure_ids,
            person_ids,
            family_ids,
            roles,
            default_filter
        )

        return pd.DataFrame.from_records(values.values())

    def get_values(
        self,
        measure_ids,
        person_ids=None,
        family_ids=None,
        roles=None,
        default_filter="apply",
    ):
        values = self.rest_client.post_measure_values(
            self.dataset_id,
            measure_ids,
            person_ids,
            family_ids,
            roles,
            default_filter
        )

        return values

    def get_instrument_values_df(
        self, instrument_id, person_ids=None, family_ids=None, roles=None
    ):
        instrument_values = self.rest_client.post_instrument_values(
            self.dataset_id,
            instrument_id,
            person_ids,
            family_ids,
            roles,
        )

        return pd.DataFrame.from_records(instrument_values.values())

    def get_instrument_values(
        self, instrument_id, person_ids=None, family_ids=None, roles=None
    ):
        instrument_values = self.rest_client.post_instrument_values(
            self.dataset_id,
            instrument_id,
            person_ids,
            family_ids,
            roles,
        )

        return instrument_values

    @property
    def instruments(self):
        if self._instruments is None:
            self._instruments = OrderedDict()
            instruments = self.rest_client.get_instrument_details(
                self.dataset_id)
            for name, instrument in instruments.items():
                measures = [
                    Measure.from_json(m) for m in instrument["measures"]
                ]
                self._instruments[name] = Instrument(name, measures)
        return self._instruments
