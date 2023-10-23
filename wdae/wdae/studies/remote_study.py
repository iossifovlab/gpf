from typing import Optional, Generator, Any, cast

from remote.rest_api_client import RESTClient

from dae.utils.regions import Region
from dae.configuration.gpf_config_parser import FrozenBox
from dae.variants.variant import SummaryVariant
from dae.variants.family_variant import FamilyVariant
from dae.studies.study import GenotypeData
from dae.pedigrees.family import Person, Family
from dae.pedigrees.families_data import FamiliesData, tag_families_data
from dae.person_sets import PersonSetCollection


class RemoteGenotypeData(GenotypeData):
    """Represent remote genotype data."""

    def __init__(self, study_id: str, rest_client: RESTClient):
        self._remote_study_id = study_id
        self.rest_client = rest_client

        config = self.rest_client.get_dataset_config(self._remote_study_id)
        if config is None:
            raise ValueError(f"unable to find remote study {study_id}")

        config["id"] = self.rest_client.prefix_remote_identifier(study_id)
        config["name"] = self.rest_client.prefix_remote_name(
            config.get("name", self._remote_study_id)
        )
        config["phenotype_tool"] = False
        config["description_editable"] = False
        if config["gene_browser"]:
            config["gene_browser"]["enabled"] = False

        if config["parents"]:
            config["parents"] = list(
                map(
                    self.rest_client.prefix_remote_identifier,
                    config["parents"]
                )
            )
            self._parents = set(config["parents"])

        if config.get("studies") is not None:
            raise ValueError("Tried to create remote dataset")

        super().__init__(FrozenBox(config), [self])

        self.is_remote = True

        self._families: FamiliesData
        self.build_families()
        self._description = ""

    def build_families(self) -> None:
        """Construct remote genotype data families."""
        families = {}
        families_details = self.rest_client.get_all_family_details(
            self._remote_study_id
        )
        for family in families_details:
            family_id = family["family_id"]
            person_jsons = family["members"]
            family_members = []
            for person_json in person_jsons:
                family_members.append(Person(**person_json))
            families[family_id] = Family.from_persons(family_members)
        self._families = FamiliesData.from_families(families)
        tag_families_data(self._families)
        pscs_config = self.config.get("person_set_collections")
        self._person_set_collections = \
            self._build_person_set_collections(pscs_config, self._families)

    def _build_person_set_collections(
        self, pscs_config: Optional[dict[str, Any]],
        families: FamiliesData
    ) -> dict[str, PersonSetCollection]:

        if pscs_config is None:
            return {}
        result = {}
        configs = self.rest_client.get_person_set_collection_configs(
            self._remote_study_id
        )
        for conf in configs.values():
            psc = PersonSetCollection.from_families(conf, self._families)
            result[psc.id] = psc
        return result

    def _build_person_set_collection(
        self, psc_config: dict[str, Any],
        families: FamiliesData
    ) -> PersonSetCollection:
        raise NotImplementedError()

    def get_studies_ids(self, leaves: bool = True) -> list[str]:
        return [self.study_id]

    @property
    def is_group(self) -> bool:
        return "studies" in self.config

    @property
    def families(self) -> FamiliesData:
        return self._families

    def query_variants(
        self,
        regions: Optional[list[Region]] = None,
        genes: Optional[list[str]] = None,
        effect_types: Optional[list[str]] = None,
        family_ids: Optional[list[str]] = None,
        person_ids: Optional[list[str]] = None,
        person_set_collection: Optional[tuple[str, list[str]]] = None,
        inheritance: Optional[str] = None,
        roles: Optional[str] = None,
        sexes: Optional[str] = None,
        variant_type: Optional[str] = None,
        real_attr_filter: Optional[list[tuple]] = None,
        ultra_rare: Optional[bool] = None,
        frequency_filter: Optional[dict] = None,
        return_reference: Optional[bool] = None,
        return_unknown: Optional[bool] = None,
        limit: Optional[int] = None,
        study_filters: Optional[list[str]] = None,
        pedigree_fields: Optional[list[str]] = None,
        unique_family_variants: bool = True,
        **kwargs: Any,
    ) -> Generator[FamilyVariant, None, None]:
        # pylint: disable=too-many-arguments,too-many-locals
        raise NotImplementedError()

    def query_summary_variants(
        self,
        regions: Optional[list[Region]] = None,
        genes: Optional[list[str]] = None,
        effect_types: Optional[list[str]] = None,
        variant_type: Optional[str] = None,
        real_attr_filter: Optional[list[tuple]] = None,
        ultra_rare: Optional[bool] = None,
        frequency_filter: Optional[dict] = None,
        return_reference: Optional[bool] = None,
        return_unknown: Optional[bool] = None,
        limit: Optional[int] = None,
        study_filters: Optional[list[str]] = None,
        **kwargs: Any
    ) -> Generator[SummaryVariant, None, None]:
        # pylint: disable=too-many-arguments
        raise NotImplementedError()

    @property
    def person_set_collection_configs(self) -> Optional[dict[str, Any]]:
        return cast(
            dict[str, Any],
            self.rest_client.get_person_set_collection_configs(
                self._remote_study_id)
        )

    def get_person_set_collection(
        self, person_set_collection_id: str
    ) -> PersonSetCollection:
        if person_set_collection_id is None:
            return None
        return self._person_set_collections[person_set_collection_id]
