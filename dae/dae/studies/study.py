from concurrent.futures import ThreadPoolExecutor, as_completed
import functools
from typing import Dict
from dae.pedigrees.family import Family, FamiliesData
from dae.person_sets import PersonSetCollection


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
        self.person_set_collections: Dict[str, PersonSetCollection] = dict()
        self.person_set_collection_configs = dict()

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
        **kwargs,
    ):
        raise NotImplementedError()

    def get_studies_ids(self):
        raise NotImplementedError()

    @property
    def families(self):
        raise NotImplementedError()

    def _build_person_set_collection(self, person_set_collection_id):
        raise NotImplementedError()

    def _build_person_set_collections(self):
        collections_config = self.config.person_set_collections
        if collections_config:
            selected_collections = \
                collections_config.selected_person_set_collections or []
            for collection_id in selected_collections:
                self._build_person_set_collection(collection_id)

            # build person set collection configs
            for collection_id, collection in \
                    self.person_set_collections.items():
                domain = list()
                for person_set in collection.person_sets.values():
                    if person_set.persons:
                        domain.append({
                            "id": person_set.id,
                            "name": person_set.name,
                            "value": person_set.value,
                            "color": person_set.color,
                        })
                collection_conf = {
                    "id": collection.id,
                    "name": collection.name,
                    "domain": domain
                }
                self.person_set_collection_configs[collection_id] = \
                    collection_conf

    def get_person_set_collection(self, person_set_collection_id):
        if person_set_collection_id is None:
            return None
        return self.person_set_collections[person_set_collection_id]


class GenotypeDataGroup(GenotypeData):
    def __init__(self, genotype_data_group_config, studies):
        super(GenotypeDataGroup, self).__init__(
            genotype_data_group_config, studies
        )
        self._families = self._build_families()
        self._build_person_set_collections()
        self._executor = None

    @property
    def executor(self):
        if self._executor is None:
            self._executor = ThreadPoolExecutor(max_workers=len(self.studies))
        return self._executor

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
            **kwargs):

        variants_futures = list()

        def get_variants(genotype_data_study):
            return genotype_data_study.query_variants(
                regions=regions,
                genes=genes,
                effect_types=effect_types,
                family_ids=family_ids,
                person_ids=person_ids,
                person_set_collection=person_set_collection,
                inheritance=inheritance,
                roles=roles,
                sexes=sexes,
                variant_type=variant_type,
                real_attr_filter=real_attr_filter,
                ultra_rare=ultra_rare,
                return_reference=return_reference,
                return_unknown=return_unknown,
                limit=limit,
                study_filters=study_filters,
                **kwargs,
            )

        for genotype_data_study in self.studies:
            future = self.executor.submit(get_variants, genotype_data_study)
            variants_futures.append(future)

        seen = set()
        for future in as_completed(variants_futures):
            for v in future.result():
                if v.fvuid in seen:
                    continue
                seen.add(v.fvuid)
                yield v
                if limit and len(seen) >= limit:
                    return

    def get_studies_ids(self):
        # TODO Use the 'cached' property on this
        return [genotype_data_study.id for genotype_data_study in self.studies]

    def _build_families(self):
        return FamiliesData.from_families(
            functools.reduce(
                lambda x, y: GenotypeDataGroup._combine_families(x, y),
                [
                    genotype_data_study.families
                    for genotype_data_study in self.studies
                ],
            )
        )

    @staticmethod
    def _combine_families(first, second):
        same_families = set(first.keys()) & set(second.keys())
        combined_dict = {}
        combined_dict.update(first)
        combined_dict.update(second)
        for sf in same_families:
            combined_dict[sf] = Family.merge(first[sf], second[sf])
        return combined_dict

    def _build_person_set_collection(self, person_set_collection_id):
        assert person_set_collection_id in \
            self.config.person_set_collections.selected_person_set_collections

        collections = list()
        for study in self.studies:
            collections.append(study.get_person_set_collection(
                person_set_collection_id
            ))

        sample_collection = self.studies[0].get_person_set_collection(
            person_set_collection_id
        )

        self.person_set_collections[person_set_collection_id] = \
            PersonSetCollection.merge(
                collections,
                self.families,
                person_set_collection_id,
                sample_collection.name
            )


class GenotypeDataStudy(GenotypeData):
    def __init__(self, config, backend):
        super(GenotypeDataStudy, self).__init__(config, [self])

        self._backend = backend
        self._build_person_set_collections()

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
            **kwargs):

        if len(kwargs):
            # FIXME This will remain so it can be used for discovering
            # when excess kwargs are passed in order to fix such cases.
            print("received excess keyword arguments when querying variants!")
            print("kwargs received: {}".format(list(kwargs.keys())))

        if study_filters and self.name not in study_filters:
            return

        person_ids = self._transform_person_set_collection_query(
            person_set_collection, person_ids)

        if person_ids is not None and len(person_ids) == 0:
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

    def _transform_person_set_collection_query(
            self, person_set_collection, person_ids):

        if person_set_collection is not None:
            person_set_collection_id, selected_person_sets = \
                person_set_collection
            selected_person_sets = set(selected_person_sets)
            person_set_collection = self.get_person_set_collection(
                person_set_collection_id)
            person_set_ids = set(person_set_collection.person_sets.keys())
            selected_person_sets = person_set_ids & selected_person_sets

            if selected_person_sets == person_set_ids:
                # all persons selected
                pass
            else:
                selected_person_ids = set()
                for set_id in selected_person_sets:
                    selected_person_ids.update(
                        person_set_collection.
                        person_sets[set_id].persons.keys()
                    )
                if person_ids is not None:
                    person_ids = set(person_ids) & selected_person_ids
                else:
                    person_ids = selected_person_ids
        return person_ids

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
