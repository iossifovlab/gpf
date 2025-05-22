from collections.abc import Generator, Iterable
from typing import Any, cast

from dae.common_reports.common_report import CommonReport
from dae.configuration.gpf_config_parser import FrozenBox
from dae.pedigrees.families_data import FamiliesData
from dae.pedigrees.family import Family, FamilyTag, Person
from dae.person_sets import (
    PersonSetCollection,
    PSCQuery,
)
from dae.person_sets.person_sets import parse_person_set_collection_config
from dae.studies.study import GenotypeDataStudy
from dae.utils.regions import Region
from dae.variants.family_variant import FamilyVariant
from dae.variants.variant import SummaryVariant
from federation.rest_api_client import RESTClient


class RemoteGenotypeData(GenotypeDataStudy):
    """Represent remote genotype data."""

    def __init__(self, config: dict, rest_client: RESTClient):
        self.remote_study_id = config["id"]
        self.rest_client = rest_client

        config["id"] = self.rest_client.prefix_remote_identifier(config["id"])
        config["name"] = self.rest_client.prefix_remote_name(
            config.get("name", self.remote_study_id),
        )
        config["phenotype_tool"] = False
        if config["phenotype_data"]:
            config["phenotype_data"] = \
                self.rest_client.prefix_remote_identifier(config["phenotype_data"])

        config["description_editable"] = False
        if config.get("gene_browser"):
            config["gene_browser"]["enabled"] = False

        if config["parents"]:
            config["parents"] = list(
                map(
                    self.rest_client.prefix_remote_identifier,
                    config["parents"],
                ),
            )

        self.config = FrozenBox(config)

        self._families: FamiliesData | None = None

        self._common_report: CommonReport | None = None
        self._remote_common_report = None

        super().__init__(self.config, None)

        self._parents = set(config["parents"])

        self.is_remote = True
        self._description = ""

    @property
    def common_report(self) -> CommonReport | None:
        """Property to lazily provide the common report."""
        if self._remote_common_report is None:
            self._remote_common_report = self.rest_client.get_common_report(
                self.remote_study_id, full=True)
            if "id" in self._remote_common_report:
                self._common_report = CommonReport(self._remote_common_report)
        return self._common_report

    @property
    def families(self) -> FamiliesData:
        if self._families is None:
            self._families = self.build_families()
        return self._families

    def build_families(self) -> FamiliesData:
        """Construct remote genotype data families."""
        families = {}
        families_details = self.rest_client.get_all_family_details(
            self.remote_study_id,
        )

        result = FamiliesData()

        for family in families_details:
            family_id = family["family_id"]
            person_jsons = family["members"]
            family_members = []
            for person_json in person_jsons:
                person = Person(**person_json)
                family_members.append(person)
                result.persons_by_person_id[person.person_id].append(person)
                result.persons[person.fpid] = person

            family_obj = Family.from_persons(family_members)
            for tag in family["tags"]:
                family_obj.set_tag(FamilyTag.from_label(tag))
            families[family_id] = family_obj

        # Setting the families directly since we can assume that
        # the remote has carried out all necessary transformations
        result._families = families  # noqa: SLF001

        return result

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
            psc = PersonSetCollection.from_families(psc_config, self.families)
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
        return False

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
        self, person_set_collection_id: str | None,
    ) -> PersonSetCollection | None:
        if person_set_collection_id is None:
            return None
        return self._person_set_collections[person_set_collection_id]

    def get_common_report(self) -> CommonReport | None:
        return self.common_report


class RemoteGenotypeDataGroup(RemoteGenotypeData):
    """Represents remote genotype data group."""

    @property
    def is_group(self) -> bool:
        return True

    def get_studies_ids(
        self, *,
        leaves: bool = True,
    ) -> list[str]:
        result = [self.study_id]
        for study in self.studies:
            result.append(study.study_id)
            if leaves:
                result.extend([
                    child_id
                    for child_id in study.get_studies_ids(leaves=True)
                    if child_id not in result
                ])
        return result
