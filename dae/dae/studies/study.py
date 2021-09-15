import time
import logging
import threading
import queue

# from dae.utils.debug_closing import closing
from contextlib import closing

from concurrent.futures import ThreadPoolExecutor

from abc import ABC, abstractmethod, abstractproperty

from typing import Dict

from dae.backends.query_runners import QueryResult
from dae.pedigrees.family import FamiliesData
from dae.person_sets import PersonSetCollection
from dae.utils.effect_utils import expand_effect_types


logger = logging.getLogger(__name__)


class GenotypeData(ABC):
    def __init__(self, config, studies):
        self.config = config
        self.studies = studies

        self._description = None

        self._person_set_collections: Dict[str, PersonSetCollection] = dict()
        self._person_set_collection_configs = dict()
        self._parents = set()
        self._executor = None

    @property
    def executor(self):
        if self._executor is None:
            self._executor = ThreadPoolExecutor(
                max_workers=len(self.studies) + 1)
        return self._executor

    def close(self):
        logger.error(f"base genotype data close() called for {self.study_id}")

    @property
    def study_id(self):
        return self.config["id"]

    @property
    def id(self):
        return self.study_id

    @property
    def name(self):
        name = self.config.get("name")
        if name:
            return name
        return self.study_id

    @property
    def description(self):
        if self._description is None:
            if self.config.description_file:
                with open(self.config.description_file, "r") as infile:
                    self._description = infile.read()
            else:
                self._description = self.config.description
        return self._description

    @property
    def year(self):
        return self.config.get("year")

    @property
    def pub_med(self):
        return self.config.get("pub_med")

    @property
    def phenotype(self):
        return self.config.get("phenotype")

    @property
    def has_denovo(self):
        return self.config.get("has_denovo")

    @property
    def has_transmitted(self):
        return self.config.get("has_transmitted")

    @property
    def has_cnv(self):
        return self.config.get("has_cnv")

    @property
    def has_complex(self):
        return self.config.get("has_complex")

    @property
    def study_type(self):
        return self.config.get("study_type")

    @property
    def parents(self):
        return self._parents

    @property
    def person_set_collections(self):
        return self._person_set_collections

    @property
    def person_set_collection_configs(self):
        return self._person_set_collection_configs

    def _add_parent(self, genotype_data_id):
        self._parents.add(genotype_data_id)

    @abstractproperty
    def is_group(self):
        pass

    @abstractmethod
    def get_studies_ids(self, leaves=True):
        pass

    def get_leaf_children(self):
        if not self.is_group:
            return []
        result = []
        seen = set()
        for study in self.studies:
            if not study.is_group:
                if study.study_id in seen:
                    continue
                result.append(study)
                seen.add(study.study_id)
            else:
                children = study.get_leaf_children()
                for child in children:
                    if child.study_id in seen:
                        continue
                    result.append(child)
                    seen.add(child.study_id)
        return result

    def _get_query_children(self, study_filters):
        leafs = []
        if self.is_group:
            leafs = self.get_leaf_children()
        else:
            leafs = [self]
        logger.debug(f"leaf children: {leafs}")
        logger.debug(f"study_filters: {study_filters}")

        if study_filters:
            leafs = [st for st in leafs if st.study_id in study_filters]
        logger.debug(f"studies to query: {leafs}")
        return leafs

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
            unique_family_variants=True,
            **kwargs):

        person_ids = self._transform_person_set_collection_query(
            person_set_collection, person_ids)
        if person_ids is not None and len(person_ids) == 0:
            return

        if effect_types:
            effect_types = expand_effect_types(effect_types)

        runners = []
        for genotype_study in self._get_query_children(study_filters):
            runner = genotype_study._backend\
                .build_family_variants_query_runner(
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
                    affected_status=affected_status,
                    **kwargs)

            study_name = genotype_study.name
            study_phenotype = genotype_study.study_phenotype

            def adapt_study_variants(v):
                if v is None:
                    return None
                for allele in v.alleles:
                    if allele.get_attribute("study_name") is None:
                        allele.update_attributes(
                            {"study_name": study_name})
                    if allele.get_attribute("study_phenotype") is None:
                        allele.update_attributes(
                            {"study_phenotype": study_phenotype})
                return v

            runner.adapt(adapt_study_variants)

            runners.append(runner)

        if len(runners) == 0:
            return

        try:
            executor = ThreadPoolExecutor(max_workers=len(runners))

            results_queue = queue.Queue(maxsize=1_000)
            result = QueryResult(results_queue, runners)
            result.start(executor)
            started = time.time()

            with closing(result) as result:
                seen = set()

                for v in result:
                    if v is None:
                        continue
                    if unique_family_variants and v.fvuid in seen:
                        continue
                    for allele in v.alleles:
                        if allele.get_attribute("study_name") is None:
                            allele.update_attributes(
                                {"study_name": self.name})
                        if allele.get_attribute("study_phenotype") is None:
                            allele.update_attributes(
                                {"study_phenotype": self.study_phenotype})

                    seen.add(v.fvuid)
                    yield v
                    if limit and len(seen) >= limit:
                        break

            elapsed = time.time() - started
            logger.info(
                f"processing study {self.study_id} "
                f"elapsed: {elapsed:.3f}")
        finally:
            logger.debug(f"shutdown thread pool executor for {self.study_id}")
            executor.shutdown(wait=True)
            logger.debug("[DONE] shutdown...")

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
        **kwargs,
    ):
        logger.info(f"summary query - study_filters: {study_filters}")
        logger.info(
            f"study {self.study_id} children: {self.get_leaf_children()}")

        person_ids = self._transform_person_set_collection_query(
            person_set_collection, person_ids)
        if person_ids is not None and len(person_ids) == 0:
            return

        if effect_types:
            effect_types = expand_effect_types(effect_types)

        runners = []
        for genotype_study in self._get_query_children(study_filters):
            runner = genotype_study._backend \
                .build_summary_variants_query_runner(
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
                    **kwargs
                )
            runner._owner = self
            runners.append(runner)

        if len(runners) == 0:
            return

        try:
            executor = ThreadPoolExecutor(max_workers=len(runners))

            results_queue = queue.Queue(maxsize=1_000)
            result = QueryResult(results_queue, runners)
            result.start(executor)
            started = time.time()

            variants = dict()
            with closing(result) as result:

                for v in result:
                    if v is None:
                        continue

                    if v.svuid in variants:
                        existing = variants[v.svuid]
                        fv_count = existing.get_attribute(
                            "family_variants_count")[0]
                        if fv_count is None:
                            continue
                        fv_count += v.get_attribute("family_variants_count")[0]
                        seen_in_status = existing.get_attribute(
                            "seen_in_status")[0]
                        seen_in_status = \
                            seen_in_status | \
                            v.get_attribute("seen_in_status")[0]

                        seen_as_denovo = existing.get_attribute(
                            "seen_as_denovo")[0]
                        seen_as_denovo = \
                            seen_as_denovo or \
                            v.get_attribute("seen_as_denovo")[0]
                        new_attributes = {
                            "family_variants_count": [fv_count],
                            "seen_in_status": [seen_in_status],
                            "seen_as_denovo": [seen_as_denovo]
                        }
                        v.update_attributes(new_attributes)

                    variants[v.svuid] = v
                    if limit and len(variants) >= limit:
                        return

            elapsed = time.time() - started
            logger.info(
                f"processing study {self.study_id} "
                f"elapsed: {elapsed:.3f}"
            )
            for v in variants.values():
                yield v
        finally:
            executor.shutdown(wait=True)

    @abstractproperty
    def families(self):
        pass

    @abstractmethod
    def _build_person_set_collection(self, person_set_collection_id):
        pass

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
                            "values": person_set.values,
                            "color": person_set.color,
                        })
                collection_conf = {
                    "id": collection.id,
                    "name": collection.name,
                    "domain": domain
                }
                self.person_set_collection_configs[collection_id] = \
                    collection_conf

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

    def get_person_set_collection(self, person_set_collection_id):
        if person_set_collection_id is None:
            return None
        return self.person_set_collections[person_set_collection_id]


class GenotypeDataGroup(GenotypeData):

    _EXECUTOR_LOCK = threading.Lock()
    EXECUTOR = None

    def __init__(self, genotype_data_group_config, studies):
        super(GenotypeDataGroup, self).__init__(
            genotype_data_group_config, studies
        )
        self._families = self._build_families()
        self._build_person_set_collections()
        self._executor = None
        self.is_remote = False
        for study in self.studies:
            study._add_parent(self.study_id)

    @property
    def is_group(self):
        return True

    @property
    def executor(self):
        with self._EXECUTOR_LOCK:
            if self.EXECUTOR is None:
                self.EXECUTOR = ThreadPoolExecutor(max_workers=6)
            return self.EXECUTOR

    @property
    def families(self):
        return self._families

    def get_studies_ids(self, leaves=True):
        if not leaves:
            return [st.study_id for st in self.studies]
        else:
            result = []
            for st in self.studies:
                result.extend(st.get_studies_ids())
            return result

    def _build_families(self):
        return FamiliesData.combine_studies(self.studies)

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

        self.is_remote = False

    @property
    def study_phenotype(self):
        return self.config.get("study_phenotype", "-")

    @property
    def is_group(self):
        return False

    def get_studies_ids(self, leaves=True):
        return [self.study_id]

    @property
    def families(self):
        return self._backend.families

    def _build_person_set_collection(self, person_set_collection_id):
        collection_config = getattr(
            self.config.person_set_collections, person_set_collection_id
        )
        self.person_set_collections[person_set_collection_id] = \
            PersonSetCollection.from_families(collection_config, self.families)
