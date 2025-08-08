import logging
import os
from collections import OrderedDict
from collections.abc import Generator, Iterable
from typing import Any, cast

import pandas as pd
from dae.common_reports.common_report import CommonReport
from dae.pedigrees.families_data import FamiliesData
from dae.person_sets.person_sets import (
    PersonSetCollection,
    PersonSetCollectionConfig,
)
from dae.pheno.common import ImportManifest, MeasureType
from dae.pheno.pheno_data import Instrument, Measure, PhenotypeData
from dae.variants.attributes import Role

from federation.utils import prefix_remote_identifier, prefix_remote_name
from rest_client.rest_client import RESTClient

logger = logging.getLogger(__name__)


class RemotePhenotypeData(PhenotypeData):
    """Phenotype data adapter for accessing remote instance phenotype data."""

    def __init__(
        self, config: dict[str, Any], rest_client: RESTClient,
    ):  # pylint: disable=super-init-not-called
        self._remote_pheno_id = config["id"]
        self.rest_client = rest_client
        self._pheno_id = prefix_remote_identifier(
            config["id"], self.rest_client,
        )

        config["name"] = prefix_remote_name(
            config.get("name", self._pheno_id), self.rest_client,
        )

        self._common_report: CommonReport | None = None
        self._remote_common_report: dict[str, Any] | None = None
        self._is_group = False
        if config.get("studies"):
            self._is_group = True
            config["studies"] = [
                prefix_remote_identifier(study_id, self.rest_client)
                for study_id in config["studies"]
            ]

        super().__init__(self._pheno_id, config)
        config["id"] = prefix_remote_identifier(config["id"], self.rest_client)

    def _build_person_set_collection(
        self,
        psc_config: PersonSetCollectionConfig,
        families: FamiliesData,
    ) -> PersonSetCollection:
        raise NotImplementedError

    def generate_import_manifests(self) -> list[ImportManifest]:
        """Collect all manifests in a phenotype data instance."""
        raise NotImplementedError

    def get_pedigree_df(self) -> pd.DataFrame:
        raise NotImplementedError

    def get_persons_df(self) -> pd.DataFrame:
        raise NotImplementedError

    @property
    def measures(self) -> dict[str, Measure]:
        if not self._measures:
            self._measures = self.get_measures()
        return self._measures

    def get_persons_values_df(
        self,
        measure_ids: Iterable[str],
        person_ids: Iterable[str] | None = None,
        family_ids: Iterable[str] | None = None,
        roles: Iterable[Role] | None = None,
        _default_filter: str = "apply",
    ) -> pd.DataFrame:
        """Get values for a list of measures for a list of persons."""
        roles_los: Iterable[str] | None = None
        if roles:
            roles_los = [r.name for r in roles]
        persons = self.rest_client.post_measures_values(
            self._remote_pheno_id,
            measure_ids=measure_ids,
            person_ids=person_ids,
            family_ids=family_ids,
            roles=roles_los,
        )
        return pd.DataFrame.from_records(persons.values())

    def has_measure(self, measure_id: str) -> bool:
        measure = self.rest_client.get_measure(
            self._remote_pheno_id, measure_id,
        )

        return measure is not None

    def get_measure(self, measure_id: str) -> Measure:
        measure = self.rest_client.get_measure(
            self._remote_pheno_id, measure_id,
        )

        return Measure.from_record(measure)

    def get_measure_description(self, measure_id: str) -> dict[str, Any]:
        measure_description = self.rest_client.get_measure_description(
            self._remote_pheno_id, measure_id)

        return cast(dict[str, Any], measure_description)

    def get_measures(
        self,
        instrument_name: str | None = None,
        measure_type: MeasureType | None = None,
    ) -> dict[str, Measure]:
        measures = self.rest_client.get_measures(
            self._remote_pheno_id,
            instrument_name,
            measure_type,
        )
        return {m["measureName"]: Measure.from_record(m) for m in measures}

    def count_measures(
        self, instrument: str | None,
        search_term: str | None,
        page: int | None = None,  # noqa: ARG002
    ) -> int:
        return self.rest_client.get_browser_measure_count(
            self._remote_pheno_id, instrument, search_term,
        )

    def get_children_ids(
        self, *,
        leaves: bool = True,  # noqa: ARG002
    ) -> list[str]:
        if not self._is_group:
            return [self.pheno_id]
        return cast(list[str], self.config["studies"])

    def get_people_measure_values(  # type: ignore
        self,
        measure_ids: Iterable[str],
        person_ids: Iterable[str] | None = None,
        family_ids: Iterable[str] | None = None,
        roles: Iterable[str] | None = None,
    ) -> dict[str, Any]:
        if person_ids is not None:
            logger.warning("Unsupported argument used: person_ids")
        if family_ids is not None:
            logger.warning("Unsupported argument used: family_ids")
        if roles is not None:
            logger.warning("Unsupported argument used: roles")

        return cast(dict[str, Any], self.rest_client.post_measures_values(
            self._remote_pheno_id, measure_ids=measure_ids))

    @property
    def instruments(self) -> dict[str, Instrument]:
        if self._instruments is None:
            self._instruments = OrderedDict()
            instruments = self.rest_client.get_instruments_details(
                self._remote_pheno_id)
            for name, instrument in instruments.items():
                measures = [
                    Measure.from_record(m) for m in instrument["measures"]
                ]
                instrument = Instrument(name)
                instrument.measures = {m.measure_id: m for m in measures}
                self._instruments[name] = instrument
        return self._instruments

    def get_instruments(self) -> list[str]:
        return cast(
            list[str],
            self.rest_client.get_instruments(self._remote_pheno_id),
        )

    def get_regressions(self) -> dict[str, Any]:
        return cast(
            dict[str, Any],
            self.rest_client.get_regressions(self._remote_pheno_id),
        )

    @property
    def common_report(self) -> CommonReport | None:
        """Property to lazily provide the common report."""
        if self._remote_common_report is None:
            self._remote_common_report = self.rest_client.get_common_report(
                self._remote_pheno_id, full=True)
            assert self._remote_common_report is not None
            if "id" in self._remote_common_report:
                self._common_report = CommonReport(self._remote_common_report)
        return self._common_report

    def get_common_report(self) -> CommonReport | None:
        return self.common_report

    @staticmethod
    def _extract_pheno_dir(url: str) -> str:
        """Extract the pheno directory from a measures info URL."""
        url = url.strip("/")
        return url[url.rindex("/") + 1:]

    def get_measures_info(self) -> dict[str, Any]:
        output = self.rest_client.get_browser_measures_info(
            self._remote_pheno_id,
        )
        pheno_folder = self._extract_pheno_dir(output["base_image_url"])
        gpf_prefix = os.environ.get("GPF_PREFIX")
        if gpf_prefix:
            gpf_prefix = gpf_prefix.strip("/")
            gpf_prefix = f"/{gpf_prefix}"

        output["base_image_url"] = (
            f"{gpf_prefix}"
            f"/api/v3/pheno_browser/images/{self.pheno_id}/"
            f"{pheno_folder}/"
        )
        return cast(dict[str, Any], output)

    def get_image(self, image_path: str) -> tuple[bytes | None, str | None]:
        """Return binary image data with mimetype."""
        image, mimetype = self.rest_client.get_pheno_image(image_path)
        if image is None or mimetype is None:
            raise ValueError(
                f"Cannot get remote image at {image_path} for "
                f"{self._remote_pheno_id} with remote pheno"
                f"{self._remote_pheno_id}",
            )
        return image, mimetype

    def search_measures(
        self,
        instrument: str | None,
        search_term: str | None,
        page: int | None = None,
        sort_by: str | None = None,
        order_by: str | None = None,
    ) -> Generator[dict[str, Any], None, None]:
        measures = self.rest_client.get_browser_measures(
            self._remote_pheno_id,
            instrument=instrument,
            search_term=search_term,
            page=page,
            sort_by=sort_by,
            order_by=order_by,
        )
        yield from measures
