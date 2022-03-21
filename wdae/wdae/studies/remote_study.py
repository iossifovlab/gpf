from dae.configuration.gpf_config_parser import FrozenBox
from dae.studies.study import GenotypeData
from dae.pedigrees.family import Person, Family, FamiliesData
from dae.person_sets import PersonSetCollection


class RemoteGenotypeData(GenotypeData):

    def __init__(self, study_id, rest_client):
        self._remote_study_id = study_id
        self.rest_client = rest_client

        config = self.rest_client.get_dataset_config(self._remote_study_id)
        config["id"] = self.rest_client.prefix_remote_identifier(study_id)
        config["name"] = self.rest_client.prefix_remote_name(
            config.get("name", self._remote_study_id)
        )

        if config["parents"]:
            config["parents"] = list(
                map(
                    self.rest_client.prefix_remote_identifier,
                    config["parents"]
                )
            )
            self._parents = list(config["parents"])

        self._study_ids = []
        if config.get("studies"):
            config["studies"] = list(
                map(
                    self.rest_client.prefix_remote_identifier,
                    config["studies"]
                )
            )
            self._study_ids = config["studies"]

        super().__init__(FrozenBox(config), [self])

        self.is_remote = True

        self._families = None

        self._build_families()

        self._person_set_collections = None

        self._build_person_set_collections()

    def _build_families(self):
        families = dict()
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

    def _build_person_set_collection(self, person_set_collection_id):
        raise NotImplementedError()

    def _build_person_set_collections(self):
        person_set_collections = dict()

        configs = self.rest_client.get_person_set_collection_configs(
            self._remote_study_id
        )

        for conf in configs.values():
            psc = PersonSetCollection.from_json(conf, self._families)
            person_set_collections[psc.id] = psc

        self._person_set_collections = person_set_collections

    def get_studies_ids(self, leaves=True):
        if not leaves:
            return [st.study_id for st in self.studies]
        else:
            result = []
            for st in self.studies:
                result.extend(st.get_studies_ids())
            return result

    @property
    def description(self):
        # FIXME
        return ""

    @property
    def is_group(self):
        return len(self._study_ids)

    @property
    def families(self):
        return self._families

    def query_variants(
        self,
        regions=None,
        genes=None,
        effect_types=None,
        family_ids=None,
        person_ids=None,
        person_set_collection=None,
        inheritance=None,
        roles=None,
        sexes=None,
        variant_type=None,
        real_attr_filter=None,
        ultra_rare=None,
        return_reference=None,
        return_unknown=None,
        limit=None,
        study_filters=None,
        affected_status=None,
        **kwargs,
    ):
        raise NotImplementedError()

    def query_summary_variants(
            self,
            regions=None,
            genes=None,
            effect_types=None,
            family_ids=None,
            person_ids=None,
            person_set_collection=None,
            inheritance=None,
            roles=None,
            sexes=None,
            variant_type=None,
            real_attr_filter=None,
            ultra_rare=None,
            return_reference=None,
            return_unknown=None,
            limit=None,
            study_filters=None,
            **kwargs):
        raise NotImplementedError()

    @property
    def person_set_collection_configs(self):
        return self.rest_client.get_person_set_collection_configs(
            self._remote_study_id
        )

    def get_person_set_collection(self, person_set_collection_id):
        if person_set_collection_id is None:
            return None
        return self._person_set_collections[person_set_collection_id]
