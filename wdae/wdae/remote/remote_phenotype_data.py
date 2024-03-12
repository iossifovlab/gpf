import logging
from typing import Optional, Iterable, Union, cast, Any, Generator
from collections import OrderedDict

import pandas as pd

from remote.rest_api_client import RESTClient

from dae.pheno.pheno_data import PhenotypeData, Measure, Instrument
from dae.pedigrees.family import Person
from dae.variants.attributes import Role


logger = logging.getLogger(__name__)


class RemotePhenotypeData(PhenotypeData):
    """Phenotype data adapter for accessing remote instance phenotype data."""

    def __init__(
        self, pheno_id: str, remote_dataset_id: str, rest_client: RESTClient
    ):
        self._remote_pheno_id = pheno_id
        self.rest_client = rest_client
        pheno_id = self.rest_client.prefix_remote_identifier(pheno_id)
        super().__init__(pheno_id, None)

        self.remote_dataset_id = remote_dataset_id
        # self.measures = self.get_measures()

    @property
    def measures(self) -> dict[str, Measure]:
        if not self._measures:
            self._measures = self.get_measures()
        return self._measures

    def get_persons_df(
        self,
        roles: Union[Iterable[Role], Iterable[str], None] = None,
        person_ids: Optional[Iterable[str]] = None,
        family_ids: Optional[Iterable[str]] = None
    ) -> pd.DataFrame:

        persons = self.rest_client.post_pheno_persons(
            self.remote_dataset_id,
            cast(Iterable[str], roles),
            person_ids,
            family_ids
        )

        return pd.DataFrame.from_records(persons.values())

    def get_persons_values_df(
        self,
        measure_ids: Iterable[str],
        person_ids: Optional[Iterable[str]] = None,
        family_ids: Optional[Iterable[str]] = None,
        roles: Optional[Iterable[Role]] = None,
        default_filter: str = "apply"
    ) -> pd.DataFrame:
        roles_los: Optional[Iterable[str]] = None
        if roles:
            roles_los = [r.name for r in roles]
        persons = self.rest_client.post_measures_values(
            self.remote_dataset_id,
            measure_ids=measure_ids,
            person_ids=person_ids,
            family_ids=family_ids,
            roles=roles_los,
        )
        return pd.DataFrame.from_records(persons.values())

    def get_persons(
        self,
        roles: Union[Iterable[Role], Iterable[str], None] = None,
        person_ids: Optional[Iterable[str]] = None,
        family_ids: Optional[Iterable[str]] = None
    ) -> dict[str, Person]:
        persons = self.rest_client.post_pheno_persons(
            self.remote_dataset_id,
            cast(Optional[Iterable[str]], roles),
            person_ids,
            family_ids
        )
        for k, v in persons.items():
            persons[k] = Person(**v)

        return cast(dict[str, Person], persons)

    def has_measure(self, measure_id: str) -> bool:
        measure = self.rest_client.get_measure(
            self.remote_dataset_id, measure_id
        )

        return measure is not None

    def get_measure(self, measure_id: str) -> Measure:
        measure = self.rest_client.get_measure(
            self.remote_dataset_id, measure_id
        )

        return Measure.from_json(measure)

    def get_measure_description(self, measure_id: str) -> dict[str, Any]:
        measure_description = self.rest_client.get_measure_description(
            self.remote_dataset_id, measure_id)

        return cast(dict[str, Any], measure_description)

    def get_measures(
        self,
        instrument_name: Optional[str] = None,
        measure_type: Optional[str] = None
    ) -> dict[str, Measure]:
        measures = self.rest_client.get_measures(
            self.remote_dataset_id,
            instrument_name,
            measure_type
        )
        return {m["measureName"]: Measure.from_json(m) for m in measures}

    def get_people_measure_values(  # type: ignore
        self,
        measure_ids: Iterable[str],
        person_ids: Optional[Iterable[str]] = None,
        family_ids: Optional[Iterable[str]] = None,
        roles: Optional[Iterable[str]] = None,
    ) -> dict[str, Any]:
        if person_ids is not None:
            logger.warning("Unsupported argument used: person_ids")
        if family_ids is not None:
            logger.warning("Unsupported argument used: family_ids")
        if roles is not None:
            logger.warning("Unsupported argument used: roles")

        return cast(dict[str, Any], self.rest_client.post_measures_values(
            self.remote_dataset_id, measure_ids=measure_ids))

    @property
    def instruments(self) -> dict[str, Instrument]:
        if self._instruments is None:
            self._instruments = OrderedDict()
            instruments = self.rest_client.get_instrument_details(
                self.remote_dataset_id)
            for name, instrument in instruments.items():
                measures = [
                    Measure.from_json(m) for m in instrument["measures"]
                ]
                instrument = Instrument(name)
                instrument.measures = {m.measure_id: m for m in measures}
                self._instruments[name] = instrument
        return self._instruments

    def get_instruments(self) -> list[str]:
        return cast(
            list[str],
            self.rest_client.get_instruments(self.remote_dataset_id)
        )

    def get_regressions(self) -> dict[str, Any]:
        return cast(
            dict[str, Any],
            self.rest_client.get_regressions(self.remote_dataset_id)
        )

    @staticmethod
    def _extract_pheno_dir(url: str) -> str:
        """Extract the pheno directory from a measures info URL."""
        url = url.strip("/")
        pheno_folder = url[url.rindex("/") + 1:]
        return pheno_folder

    def get_measures_info(self) -> dict[str, Any]:
        output = self.rest_client.get_browser_measures_info(
            self.remote_dataset_id
        )
        pheno_folder = self._extract_pheno_dir(output["base_image_url"])
        output["base_image_url"] = (
            "/api/v3/pheno_browser/remote_images/"
            f"{self.rest_client.remote_id}/{pheno_folder}/"
        )
        return cast(dict[str, Any], output)

    def search_measures(
        self, instrument: Optional[str], search_term: Optional[str]
    ) -> Generator[dict[str, Any], None, None]:
        measures = self.rest_client.get_browser_measures(
            self.remote_dataset_id,
            instrument,
            search_term
        )
        for m in measures:
            yield m
