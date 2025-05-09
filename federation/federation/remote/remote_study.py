from collections.abc import Generator, Iterable
from typing import Any, cast

from dae.common_reports.common_report import CommonReport
from dae.configuration.gpf_config_parser import FrozenBox
from dae.pedigrees.families_data import FamiliesData, tag_families_data
from dae.pedigrees.family import Family, Person
from dae.person_sets import (
    PersonSetCollection,
    PSCQuery,
)
from dae.person_sets.person_sets import parse_person_set_collection_config
from dae.studies.study import GenotypeDataStudy
from dae.utils.regions import Region
from dae.variants.family_variant import FamilyVariant
from dae.variants.variant import SummaryVariant
from federation.remote.rest_api_client import RESTClient


class RemoteGenotypeData(GenotypeDataStudy):
    """Represent remote genotype data."""

    def __init__(self, study_id: str, rest_client: RESTClient):
        self.remote_study_id = study_id
        self.rest_client = rest_client

        config = self.rest_client.get_dataset_config(self.remote_study_id)
        if config is None:
            raise ValueError(f"unable to find remote study {study_id}")

        config["id"] = self.rest_client.prefix_remote_identifier(study_id)
        config["name"] = self.rest_client.prefix_remote_name(
            config.get("name", self.remote_study_id),
        )
        config["phenotype_tool"] = False
        if config["phenotype_data"]:
            config["phenotype_data"] = \
                self.rest_client.prefix_remote_identifier(config["phenotype_data"])

        config["description_editable"] = False
        if config["gene_browser"]:
            config["gene_browser"]["enabled"] = False

        if config["parents"]:
            config["parents"] = list(
                map(
                    self.rest_client.prefix_remote_identifier,
                    config["parents"],
                ),
            )
            self._parents = set(config["parents"])

        if config.get("studies") is not None:
            raise ValueError("Tried to create remote dataset")

        self.config = config

        self._families: FamiliesData
        self.build_families()

        remote_common_report = rest_client.get_common_report(
            self.remote_study_id, full=True)

        if "id" not in remote_common_report:
            self.common_report = None
        else:
            self.common_report = CommonReport(remote_common_report)

        super().__init__(FrozenBox(config), [self])

        self.is_remote = True
        self._description = ""

    def build_families(self) -> None:
        """Construct remote genotype data families."""
        families = {}
        families_details = self.rest_client.get_all_family_details(
            self.remote_study_id,
        )
        for family in families_details:
            family_id = family["family_id"]
            person_jsons = family["members"]
            family_members = [
                Person(**person_json) for person_json in person_jsons
            ]
            families[family_id] = Family.from_persons(family_members)
        self._families = FamiliesData.from_families(families)
        tag_families_data(self._families)
        pscs_config = self.config.get("person_set_collections")
        self._person_set_collections = \
            self._build_person_set_collections(pscs_config, self._families)

    # pylint: disable=arguments-renamed
    def _build_person_set_collections(  # type: ignore[override]
        self, pscs_config: dict[str, Any] | None,
        _families: FamiliesData,
    ) -> dict[str, PersonSetCollection]:

        if pscs_config is None:
            return {}
        result = {}
        configs = self.rest_client.get_person_set_collection_configs(
            self.remote_study_id,
        )
        for conf in configs.values():
            psc_config = parse_person_set_collection_config(conf)
            psc = PersonSetCollection.from_families(psc_config, self._families)
            result[psc.id] = psc
        return result

    def _build_person_set_collection(  # type: ignore[override]
        self, psc_config: dict[str, Any],
        families: FamiliesData,
    ) -> PersonSetCollection:
        raise NotImplementedError

    def get_studies_ids(
        self, *, leaves: bool = True,  # noqa: ARG002
    ) -> list[str]:
        return [self.study_id]

    @property
    def is_group(self) -> bool:
        return "studies" in self.config

    @property
    def families(self) -> FamiliesData:
        return self._families

    def query_variants(
        self,
        *,
        regions: list[Region] | None = None,
        genes: list[str] | None = None,
        effect_types: list[str] | None = None,
        family_ids: Iterable[str] | None = None,
        person_ids: Iterable[str] | None = None,
        person_set_collection: PSCQuery | None = None,
        inheritance: str | list[str] | None = None,
        roles: str | None = None,
        sexes: str | None = None,
        variant_type: str | None = None,
        real_attr_filter: list[tuple] | None = None,
        ultra_rare: bool | None = None,
        frequency_filter: list[tuple] | None = None,
        return_reference: bool | None = None,
        return_unknown: bool | None = None,
        limit: int | None = None,
        study_filters: Iterable[str] | None = None,
        unique_family_variants: bool = True,
        **kwargs: Any,
    ) -> Generator[FamilyVariant, None, None]:
        # pylint: disable=too-many-arguments,too-many-locals
        raise NotImplementedError

    def query_summary_variants(
        self,
        *,
        regions: list[Region] | None = None,
        genes: list[str] | None = None,
        effect_types: list[str] | None = None,
        variant_type: str | None = None,
        real_attr_filter: list[tuple] | None = None,
        ultra_rare: bool | None = None,
        frequency_filter: list[tuple] | None = None,
        return_reference: bool | None = None,
        return_unknown: bool | None = None,
        limit: int | None = None,
        study_filters: list[str] | None = None,
        **kwargs: Any,
    ) -> Generator[SummaryVariant, None, None]:
        # pylint: disable=too-many-arguments
        raise NotImplementedError

    @property
    def person_set_collection_configs(self) -> dict[str, Any] | None:
        return cast(
            dict[str, Any],
            self.rest_client.get_person_set_collection_configs(
                self.remote_study_id),
        )

    def get_person_set_collection(
        self, person_set_collection_id: str,
    ) -> PersonSetCollection:
        if person_set_collection_id is None:
            return None
        return self._person_set_collections[person_set_collection_id]

    def get_common_report(self) -> CommonReport | None:
        return self.common_report
