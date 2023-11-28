import logging
from collections import OrderedDict

import pandas as pd
from dae.pheno.pheno_db import PhenotypeData, Measure, Instrument
from dae.pedigrees.family import Person


logger = logging.getLogger(__name__)


class RemotePhenotypeData(PhenotypeData):
    """Phenotype data adapter for accessing remote instance phenotype data."""

    def __init__(self, pheno_id, remote_dataset_id, rest_client):
        self._remote_pheno_id = pheno_id
        self.rest_client = rest_client
        pheno_id = self.rest_client.prefix_remote_identifier(pheno_id)
        super(RemotePhenotypeData, self).__init__(pheno_id)

        self.remote_dataset_id = remote_dataset_id
        self._instruments = None
        self._measures = None
        # self.measures = self.get_measures()

    @property
    def measures(self):
        if not self._measures:
            self._measures = self.get_measures()
        return self._measures

    def get_persons_df(self, roles=None, person_ids=None, family_ids=None):
        persons = self.rest_client.post_pheno_persons(
            self.remote_dataset_id,
            roles,
            person_ids,
            family_ids
        )

        return pd.DataFrame.from_records(persons.values())

    def get_persons_values_df(
        self, measure_ids, person_ids=None, family_ids=None, roles=None
    ):
        persons = self.rest_client.post_pheno_persons_values(
            self.remote_dataset_id,
            roles,
            person_ids,
            family_ids
        )

        return pd.DataFrame.from_records(persons.values())

    def get_persons(self, roles=None, person_ids=None, family_ids=None):
        persons = self.rest_client.post_pheno_persons(
            self.remote_dataset_id,
            roles,
            person_ids,
            family_ids
        )
        for k, v in persons.items():
            persons[k] = Person(**v)

        return persons

    def has_measure(self, measure_id):
        measure = self.rest_client.get_measure(
            self.remote_dataset_id, measure_id
        )

        return measure is not None

    def get_measure(self, measure_id):
        measure = self.rest_client.get_measure(
            self.remote_dataset_id, measure_id
        )

        return Measure.from_json(measure)

    def get_measure_description(self, measure_id):
        measure_description = self.rest_client.get_measure_description(
            self.remote_dataset_id, measure_id)

        return measure_description

    def get_measures(self, instrument=None, measure_type=None):
        measures = self.rest_client.get_measures(
            self.remote_dataset_id,
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
            self.remote_dataset_id,
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
            self.remote_dataset_id,
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
            self.remote_dataset_id,
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
            self.remote_dataset_id,
            measure_ids,
            person_ids,
            family_ids,
            roles,
            default_filter
        )

        return values

    def get_instrument_values_df(
        self, instrument_name, person_ids=None,
        family_ids=None, role=None, measure_ids=None
    ):
        instrument_values = self.rest_client.post_instrument_values(
            self.remote_dataset_id,
            instrument_name,
            person_ids,
            family_ids,
            role,
            measure_ids,
        )

        return pd.DataFrame.from_records(instrument_values.values())

    def get_instrument_values(
        self, instrument_name, person_ids=None,
        family_ids=None, role=None, measure_ids=None
    ):
        instrument_values = self.rest_client.post_instrument_values(
            self.remote_dataset_id,
            instrument_name,
            person_ids,
            family_ids,
            role,
            measure_ids,
        )

        return instrument_values

    def get_people_measure_values(
        self,
        measure_ids,
        person_ids=None,
        family_ids=None,
        roles=None,
    ):
        if person_ids is not None:
            logger.warning("Unsupported argument used: person_ids")
        if family_ids is not None:
            logger.warning("Unsupported argument used: family_ids")
        if roles is not None:
            logger.warning("Unsupported argument used: roles")

        return self.rest_client.post_measures_values(
            self.remote_dataset_id, measure_ids=measure_ids)

    @property
    def instruments(self):
        if self._instruments is None:
            self._instruments = OrderedDict()
            instruments = self.rest_client.get_instrument_details(
                self.remote_dataset_id)
            for name, instrument in instruments.items():
                measures = [
                    Measure.from_json(m) for m in instrument["measures"]
                ]
                self._instruments[name] = Instrument(name, measures)
        return self._instruments

    def get_instruments(self):
        return self.rest_client.get_instruments(self.remote_dataset_id)

    def get_regressions(self):
        return self.rest_client.get_regressions(self.remote_dataset_id)

    def get_measures_info(self):
        output = self.rest_client.get_browser_measures_info(
            self.remote_dataset_id
        )
        output["base_image_url"] = \
            f"/{self.rest_client.gpf_prefix}/{output['base_image_url']}"
        return output

    def search_measures(self, instrument, search_term):
        measures = self.rest_client.get_browser_measures(
            self.remote_dataset_id,
            instrument,
            search_term
        )
        base = self.rest_client.build_host_url()
        for m in measures:
            m["measure"]["base_url"] = base
            yield m
