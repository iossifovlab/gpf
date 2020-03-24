import itertools
import functools
from typing import Dict
from dae.pedigrees.family import FamiliesData
from dae.pedigrees.families_groups import FamiliesGroups
from dae.person_sets import PersonSet, PersonSetCollection


class GenotypeData:
    def __init__(self, config, studies):
        self.config = config
        self.studies = studies

        self.id = self.config.id
        self.name = self.config.name
        if self.config.description_file:
            with open(self.config.description_file, "r") as infile:
                self.description = infile.read()
        else:
            self.description = self.config.description
        self.year = self.config.year
        self.pub_med = self.config.pub_med

        self.has_denovo = self.config.has_denovo
        self.has_transmitted = self.config.has_transmitted
        self.has_cnv = self.config.has_cnv
        self.has_complex = self.config.has_complex

        self.study_type = self.config.study_type
        self.families_groups = None
        self.person_set_collections: Dict[str, PersonSetCollection] = dict()

    def query_variants(
        self,
        regions=None,
        genes=None,
        effect_types=None,
        family_ids=None,
        person_ids=None,
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
        **kwargs,
    ):
        raise NotImplementedError()

    def get_studies_ids(self):
        raise NotImplementedError()

    @property
    def families(self):
        raise NotImplementedError()

    def _build_study_groups(self):
        if self.families_groups is None:
            config = self.config.people_group

            self.families_groups = FamiliesGroups.from_config(
                self.families, config
            )
            self.families_groups.add_predefined_groups(
                ["status", "role", "sex", "role.sex", "family_size"]
            )

    def _build_person_set_collection(self, person_set_collection_id):
        raise NotImplementedError()

    def get_families_group(self, families_group_id):
        self._build_study_groups()
        return self.families_groups.get(families_group_id)

    def get_person_set_collection(self, person_set_collection_id):
        if person_set_collection_id not in self.person_set_collections:
            self._build_person_set_collection(person_set_collection_id)
        return self.person_set_collections[person_set_collection_id]


class GenotypeDataGroup(GenotypeData):
    def __init__(self, genotype_data_group_config, studies):
        super(GenotypeDataGroup, self).__init__(
            genotype_data_group_config, studies
        )
        self._families = self._build_families()

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
        **kwargs,
    ):
        return itertools.chain(
            *[
                genotype_data_study.query_variants(
                    regions,
                    genes,
                    effect_types,
                    family_ids,
                    person_ids,
                    inheritance,
                    roles,
                    sexes,
                    variant_type,
                    real_attr_filter,
                    ultra_rare,
                    return_reference,
                    return_unknown,
                    limit,
                    study_filters,
                    **kwargs,
                )
                for genotype_data_study in self.studies
            ]
        )

    def get_studies_ids(self):
        # TODO Use the 'cached' property on this
        return [genotype_data_study.id for genotype_data_study in self.studies]

    def _build_families(self):
        return FamiliesData.from_families(
            functools.reduce(
                lambda x, y: self._combine_families(x, y),
                [
                    genotype_data_study.families
                    for genotype_data_study in self.studies
                ],
            )
        )

    def _combine_families(self, first, second):
        same_families = set(first.keys()) & set(second.keys())
        combined_dict = {}
        combined_dict.update(first)
        combined_dict.update(second)
        for sf in same_families:
            combined_dict[sf] = (
                first[sf] if len(first[sf]) > len(second[sf]) else second[sf]
            )
        return combined_dict

    def _build_person_set_collection(self, person_set_collection_id):
        assert (
            person_set_collection_id
            in self.config.person_set_collections.selected_person_set_collections
        )

        sample_collection = self.studies[0].get_person_set_collection(
            person_set_collection_id
        )
        collection_name = sample_collection.name

        new_collection = PersonSetCollection(
            person_set_collection_id, collection_name, dict(), self.families,
        )

        for study in self.studies:
            collection = study.get_person_set_collection(
                person_set_collection_id
            )
            assert new_collection.name == collection.name

            for person_set_id, person_set in collection.person_sets.items():
                if person_set_id not in new_collection.person_sets:
                    new_collection.person_sets[person_set_id] = PersonSet(
                        person_set.id,
                        person_set.name,
                        person_set.value,
                        person_set.color,
                        dict(),
                    )
                for person_id, person in person_set.persons.items():
                    if person_id in self.families.persons:
                        new_collection.person_sets[person_set_id].persons[
                            person_id
                        ] = person

        self.person_set_collections[person_set_collection_id] = new_collection


class GenotypeDataStudy(GenotypeData):
    def __init__(self, config, backend):
        super(GenotypeDataStudy, self).__init__(config, [self])

        self._backend = backend

    def query_variants(
        self,
        regions=None,
        genes=None,
        effect_types=None,
        family_ids=None,
        person_ids=None,
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
        **kwargs,
    ):

        if len(kwargs):
            # FIXME This will remain so it can be used for discovering
            # when excess kwargs are passed in order to fix such cases.
            print("received excess keyword arguments when querying variants!")
            print("kwargs received: {}".format(list(kwargs.keys())))

        if study_filters and self.name not in study_filters:
            return

        for variant in self._backend.query_variants(
            regions=regions,
            genes=genes,
            effect_types=effect_types,
            family_ids=family_ids,
            person_ids=person_ids,
            inheritance=inheritance,
            roles=roles,
            sexes=sexes,
            variant_type=variant_type,
            real_attr_filter=real_attr_filter,
            ultra_rare=ultra_rare,
            return_reference=return_reference,
            return_unknown=return_unknown,
            limit=limit,
        ):
            for allele in variant.alleles:
                allele.update_attributes({"studyName": self.name})
            yield variant

    def get_studies_ids(self):
        return [self.id]

    @property
    def families(self):
        return self._backend.families

    def _build_person_set_collection(self, person_set_collection_id):
        collection_config = getattr(
            self.config.person_set_collections, person_set_collection_id
        )
        self.person_set_collections[
            person_set_collection_id
        ] = PersonSetCollection.from_families(collection_config, self.families)
