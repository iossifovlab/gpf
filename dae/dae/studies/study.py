"""Classes to represent genotype data."""
from __future__ import annotations
import os
import time
import logging
import functools

from contextlib import closing
from os.path import basename, exists

from abc import ABC, abstractmethod

from typing import cast, Any, Optional, Generator

from box import Box

from dae.utils.regions import Region
from dae.variants.variant import SummaryVariant
from dae.variants.family_variant import FamilyVariant
from dae.query_variants.query_runners import QueryResult
from dae.pedigrees.family import FamiliesData
from dae.pedigrees.loader import FamiliesLoader
from dae.person_sets import PersonSetCollection
from dae.utils.effect_utils import expand_effect_types


logger = logging.getLogger(__name__)


# FIXME: Too many public methods, refactor?
class GenotypeData(ABC):  # pylint: disable=too-many-public-methods
    """Abstract base class for genotype data."""

    def __init__(self, config: Box, studies: list[GenotypeData]):
        self.config = config
        self.studies = studies

        self._description: Optional[str] = None

        self._person_set_collection_configs = None
        self._person_set_collections: dict[str, PersonSetCollection] = {}
        self._parents: set[str] = set()
        self._executor = None

    def close(self) -> None:
        logger.error("base genotype data close() called for %s", self.study_id)

    @property
    def study_id(self) -> str:
        return cast(str, self.config["id"])

    # @property
    # def id(self):  # pylint: disable=invalid-name
    #     return self.study_id

    @property
    def name(self) -> str:
        name = self.config.get("name")
        if name:
            return cast(str, name)
        return self.study_id

    @property
    def description(self) -> Optional[str]:
        """Load and return description of a genotype data."""
        if self._description is None:
            if basename(self.config.description_file) != "description.md" and \
                    not exists(self.config.description_file):
                # If a non-default description file was given, assert it exists
                raise ValueError(
                    f"missing description file {self.config.description_file}")

            if exists(self.config.description_file):
                # the default description file may not yet exist
                with open(
                        self.config.description_file,
                        mode="rt", encoding="utf8") as infile:
                    self._description = infile.read()
        return self._description

    @description.setter
    def description(self, input_text: str) -> None:
        self._description = None
        with open(
                self.config.description_file,
                mode="wt", encoding="utf8") as outfile:
            outfile.write(input_text)

    @property
    def year(self) -> Optional[str]:
        return cast(str, self.config.get("year"))

    @property
    def pub_med(self) -> Optional[str]:
        return cast(str, self.config.get("pub_med"))

    @property
    def phenotype(self) -> Optional[str]:
        return cast(str, self.config.get("phenotype"))

    @property
    def has_denovo(self) -> bool:
        return cast(bool, self.config.get("has_denovo"))

    @property
    def has_transmitted(self) -> bool:
        return cast(bool, self.config.get("has_transmitted"))

    @property
    def has_cnv(self) -> bool:
        return cast(bool, self.config.get("has_cnv"))

    @property
    def has_complex(self) -> bool:
        return cast(bool, self.config.get("has_complex"))

    @property
    def study_type(self) -> str:
        return cast(str, self.config.get("study_type"))

    @property
    def parents(self) -> set[str]:
        return self._parents

    @property
    def person_set_collections(self) -> dict[str, PersonSetCollection]:
        return self._person_set_collections

    @property
    def person_set_collection_configs(self) -> Optional[dict[str, Any]]:
        return self._person_set_collection_configs

    def _add_parent(self, genotype_data_id: str) -> None:
        self._parents.add(genotype_data_id)

    @property
    @abstractmethod
    def is_group(self) -> bool:
        return False

    @abstractmethod
    def get_studies_ids(self, leaves: bool = True) -> list[str]:
        pass

    def get_leaf_children(self) -> list[GenotypeDataStudy]:
        """Return list of genotype studies children of this group."""
        if not self.is_group:
            return []
        result = []
        seen = set()
        for study in self.studies:
            if not study.is_group:
                if study.study_id in seen:
                    continue
                result.append(cast(GenotypeDataStudy, study))
                seen.add(study.study_id)
            else:
                children = study.get_leaf_children()
                for child in children:
                    if child.study_id in seen:
                        continue
                    result.append(child)
                    seen.add(child.study_id)
        return result

    def _get_query_children(
        self, study_filters: Optional[list[str]]
    ) -> list[GenotypeDataStudy]:
        leafs = []
        if self.is_group:
            leafs = self.get_leaf_children()
        else:
            leafs = [cast(GenotypeDataStudy, self)]
        logger.debug("leaf children: %s", [st.study_id for st in leafs])
        logger.debug("study_filters: %s", study_filters)

        if study_filters is not None:
            leafs = [st for st in leafs if st.study_id in study_filters]
        logger.debug("studies to query: %s", [st.study_id for st in leafs])
        return leafs

    # FIXME: Too many locals, too many arguments, complex. To refactor
    def query_result_variants(
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
        real_attr_filter: Optional[dict] = None,
        ultra_rare: Optional[bool] = None,
        frequency_filter: Optional[dict]=None,
        return_reference: Optional[bool] = None,
        return_unknown: Optional[bool] = None,
        limit: Optional[int] = None,
        study_filters: Optional[list[str]] = None,
        pedigree_fields: Optional[list[str]] = None,
        **_kwargs: Any
    ) -> Optional[QueryResult]:
        """Build a query result."""
        # flake8: noqa: C901
        # pylint: disable=too-many-locals,too-many-arguments
        del pedigree_fields  # Unused argument
        if person_ids is not None and len(person_ids) == 0:
            return None

        if effect_types:
            effect_types = expand_effect_types(effect_types)

        def adapt_study_variants(
            study_name: str,
            study_phenotype: str,
            v: FamilyVariant
        ) -> FamilyVariant:
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

        runners = []
        for genotype_study in self._get_query_children(study_filters):
            person_sets_query = None
            query_person_ids = set(person_ids.copy()) \
                if person_ids is not None else None
            if person_set_collection is not None:
                collection_id, selected_person_sets = person_set_collection
                if selected_person_sets is not None:
                    collection = genotype_study\
                        .get_person_set_collection(collection_id)

                    # pylint: disable=no-member,protected-access
                    person_sets_query = genotype_study\
                        ._backend\
                        .build_person_set_collection_query(
                            collection, person_set_collection)
                    if person_sets_query == ([], []):
                        continue

                    if person_sets_query is None:
                        query_person_ids = genotype_study\
                            ._transform_person_set_collection_query(
                                person_set_collection, person_ids)

            if query_person_ids is not None and len(query_person_ids) == 0:
                logger.debug(
                    "Study %s can't match any person to filter %s... "
                    "skipping",
                    genotype_study.study_id,
                    person_set_collection)
                continue

            # pylint: disable=no-member,protected-access
            runner = genotype_study._backend\
                .build_family_variants_query_runner(
                    regions=regions,
                    genes=genes,
                    effect_types=effect_types,
                    family_ids=family_ids,
                    person_ids=query_person_ids,
                    inheritance=inheritance,
                    roles=roles,
                    sexes=sexes,
                    variant_type=variant_type,
                    real_attr_filter=real_attr_filter,
                    ultra_rare=ultra_rare,
                    frequency_filter=frequency_filter,
                    return_reference=return_reference,
                    return_unknown=return_unknown,
                    limit=limit,
                    pedigree_fields=person_sets_query)
            if runner is None:
                logger.debug(
                    "study %s has no varants... skipping",
                    genotype_study.study_id)
                continue

            runner.study_id = genotype_study.study_id
            logger.debug("runner created")

            study_name = genotype_study.name
            study_phenotype = genotype_study.study_phenotype

            runner.adapt(functools.partial(
                adapt_study_variants, study_name, study_phenotype))
            runners.append(runner)

        logger.debug("runners: %s", len(runners))
        if len(runners) == 0:
            return None

        return QueryResult(runners)

    def query_variants(  # pylint: disable=too-many-locals,too-many-arguments
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
        real_attr_filter: Optional[dict] = None,
        ultra_rare: Optional[bool] = None,
        frequency_filter: Optional[dict] = None,
        return_reference: Optional[bool] = None,
        return_unknown: Optional[bool] = None,
        limit: Optional[int] = None,
        study_filters: Optional[list[str]] = None,
        pedigree_fields: Optional[list[str]] = None,
        unique_family_variants: bool = True,
        **kwargs: Any
    ) -> Generator[FamilyVariant, None, None]:
        """Query and return generator containing variants."""
        result = self.query_result_variants(
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
            frequency_filter=frequency_filter,
            return_reference=return_reference,
            return_unknown=return_unknown,
            limit=limit,
            study_filters=study_filters,
            pedigree_fields=pedigree_fields,
            **kwargs
        )
        if result is None:
            return

        started = time.time()
        try:
            result.start()

            with closing(result) as result:
                seen = set()

                for v in result:
                    if v is None:
                        continue

                    if unique_family_variants and v.fvuid in seen:
                        continue

                    seen.add(v.fvuid)
                    yield v
                    if limit and len(seen) >= limit:
                        break

        except GeneratorExit:
            logger.info("generator closed")
        except Exception:  # pylint: disable=broad-except
            logger.exception("unexpected exception:", exc_info=True)
        finally:
            elapsed = time.time() - started
            logger.info(
                "processing study %s elapsed: %.3f", self.study_id, elapsed)

            logger.debug("[DONE] executor closed...")

    # FIXME: Too many locals, too many arguments, To refactor
    def query_result_summary_variants(
        self,
        regions: Optional[list[Region]] = None,
        genes: Optional[list[str]] = None,
        effect_types: Optional[list[str]] = None,
        # family_ids=None,
        # person_ids=None,
        # person_set_collection=None,
        # inheritance=None,
        # roles=None,
        # sexes=None,
        variant_type: Optional[str] = None,
        real_attr_filter: Optional[dict] = None,
        ultra_rare: Optional[bool] = None,
        frequency_filter: Optional[dict]=None,
        return_reference: Optional[bool] = None,
        return_unknown: Optional[bool] = None,
        limit: Optional[int] = None,
        study_filters: Optional[list[str]] = None,
        **kwargs: Any
    ) -> Optional[QueryResult]:
        # pylint: disable=too-many-locals,too-many-arguments,unused-argument
        """Build a query result for summary variants only."""
        logger.info("summary query - study_filters: %s", study_filters)
        logger.info(
            "study %s children: %s", self.study_id, self.get_leaf_children())

        # person_ids = self._transform_person_set_collection_query(
        #     person_set_collection, person_ids)
        # if person_ids is not None and len(person_ids) == 0:
        #     return None

        if effect_types:
            effect_types = expand_effect_types(effect_types)

        runners = []
        for genotype_study in self._get_query_children(study_filters):
            # pylint: disable=no-member,protected-access
            runner = genotype_study._backend \
                .build_summary_variants_query_runner(
                    regions=regions,
                    genes=genes,
                    effect_types=effect_types,
                    # family_ids=family_ids,
                    # person_ids=person_ids,
                    # inheritance=inheritance,
                    # roles=roles,
                    # sexes=sexes,
                    variant_type=variant_type,
                    real_attr_filter=real_attr_filter,
                    ultra_rare=ultra_rare,
                    frequency_filter=frequency_filter,
                    return_reference=return_reference,
                    return_unknown=return_unknown,
                    limit=limit)
            runner.study_id = genotype_study.study_id
            runners.append(runner)

        if len(runners) == 0:
            return None

        result = QueryResult(runners)
        return result

    def query_summary_variants(
        self,
        regions: Optional[list[Region]] = None,
        genes: Optional[list[str]] = None,
        effect_types: Optional[list[str]] = None,
        # family_ids=None,
        # person_ids=None,
        # person_set_collection=None,
        # inheritance=None,
        # roles=None,
        # sexes=None,
        variant_type: Optional[str] = None,
        real_attr_filter: Optional[dict] = None,
        ultra_rare: Optional[bool] = None,
        frequency_filter: Optional[dict] = None,
        return_reference: Optional[bool] = None,
        return_unknown: Optional[bool] = None,
        limit: Optional[int] = None,
        study_filters: Optional[list[str]] = None,
        **kwargs: Any
    ) -> Generator[SummaryVariant, None, None]:
        """Query and return generator containing summary variants."""
        # pylint: disable=too-many-locals,too-many-arguments
        result = self.query_result_summary_variants(
            regions=regions,
            genes=genes,
            effect_types=effect_types,
            # family_ids=family_ids,
            # person_ids=person_ids,
            # person_set_collection=person_set_collection,
            # inheritance=inheritance,
            # roles=roles,
            # sexes=sexes,
            variant_type=variant_type,
            real_attr_filter=real_attr_filter,
            ultra_rare=ultra_rare,
            frequency_filter=frequency_filter,
            return_reference=return_reference,
            return_unknown=return_unknown,
            limit=limit,
            study_filters=study_filters,
            **kwargs)
        try:
            if result is None:
                return

            started = time.time()
            variants: dict[str, Any] = {}
            with closing(result) as result:
                result.start()

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
                "processing study %s elapsed: %.3f",
                self.study_id, elapsed)

            for v in variants.values():
                yield v
        finally:
            logger.debug("[DONE] executor closed...")

    @property
    @abstractmethod
    def families(self) -> FamiliesData:
        pass

    @abstractmethod
    def _build_person_set_collection(
        self, person_set_collection_id: str
    ) -> None:
        pass

    def _build_person_set_collections(self) -> None:
        collections_config = self.config.person_set_collections
        if collections_config:
            selected_collections = \
                collections_config.selected_person_set_collections or []
            for collection_id in selected_collections:
                self._build_person_set_collection(collection_id)

    def _transform_person_set_collection_query(
        self, collection_query: tuple[str, list[str]],
        person_ids: Optional[list[str]]
    ) -> Optional[set[str]]:
        if collection_query is not None:
            collection_id, selected_sets = collection_query
            collection = self.get_person_set_collection(collection_id)
            if collection is None:
                return set(person_ids) if person_ids is not None else None
            person_set_ids = set(collection.person_sets.keys())
            if selected_sets is not None:
                selected_person_ids: set[str] = set()
                if set(selected_sets) == person_set_ids:
                    return set(person_ids) \
                        if person_ids is not None else None

                for set_id in set(selected_sets) & person_set_ids:
                    selected_person_ids.update(
                        collection.person_sets[set_id].persons.keys()
                    )
                if person_ids is not None:
                    person_ids = list(set(person_ids) & selected_person_ids)
                else:
                    person_ids = list(selected_person_ids)
        return set(fpid[1] for fpid in person_ids)

    def get_person_set_collection(
        self, person_set_collection_id: str
    ) -> Optional[PersonSetCollection]:
        if person_set_collection_id is None:
            return None
        return self.person_set_collections[person_set_collection_id]


class GenotypeDataGroup(GenotypeData):
    """
    Represents a group of genotype data classes.

    Queries to this object will be sent to all child data.
    """

    def __init__(
        self, genotype_data_group_config: Box,
        studies: list[GenotypeData]
    ):
        super().__init__(
            genotype_data_group_config, studies
        )
        self._families = self._build_families()
        self._build_person_set_collections()
        self._executor = None
        self.is_remote = False
        for study in self.studies:
            study._add_parent(self.study_id)

    @property
    def is_group(self) -> bool:
        return True

    @property
    def families(self) -> FamiliesData:
        return self._families

    def get_studies_ids(self, leaves: bool = True) -> list[str]:
        result = set([self.study_id])
        if not leaves:
            result = result.union([st.study_id for st in self.studies])
            return list(result)
        for study in self.studies:
            result = result.union(study.get_studies_ids())
        return list(result)

    def _build_families(self) -> FamiliesData:
        cache_path = os.path.join(
            self.config["conf_dir"], "families_cache.ped"
        )

        if os.path.exists(cache_path):
            try:
                result = FamiliesLoader.load_pedigree_file(cache_path)
                return result
            except BaseException:  # pylint: disable=broad-except
                logger.error(
                    "Couldn't load families cache for %s", self.study_id
                )


        logger.info(
            "building combined families from studies: %s",
            [st.study_id for st in self.studies])

        if len(self.studies) == 1:
            return FamiliesData.copy(self.studies[0].families)

        logger.info(
            "combining families from study %s and from study %s",
            self.studies[0].study_id, self.studies[1].study_id)
        result = FamiliesData.combine(
            self.studies[0].families,
            self.studies[1].families)

        if len(self.studies) > 2:
            for sind in range(2, len(self.studies)):
                logger.debug(
                    "processing study (%s): %s",
                    sind, self.studies[sind].study_id)
                logger.info(
                    "combining families from studies (%s) %s with families "
                    "from study %s",
                    sind, [st.study_id for st in self.studies[:sind]],
                    self.studies[sind].study_id)
                result = FamiliesData.combine(
                    result,
                    self.studies[sind].families,
                    forced=True)
        # pylint: disable=import-outside-toplevel
        from dae.pedigrees.family_tag_builder import FamilyTagsBuilder
        tagger = FamilyTagsBuilder()
        tagger.tag_families_data(result)
        try:
            FamiliesLoader.save_families(result, cache_path)
        except BaseException:  # pylint: disable=broad-except
            logger.exception(
                "Failed to cache families for %s", self.study_id
            )

        return result

    def _build_person_set_collection(
        self, person_set_collection_id: str
    ) -> None:
        assert person_set_collection_id in \
            self.config.person_set_collections.selected_person_set_collections

        collections = []
        for study in self.studies:
            study_collection = study.get_person_set_collection(
                person_set_collection_id)
            if study_collection is None:
                raise ValueError(
                    f"person set collection {person_set_collection_id} "
                    f"not found in study {study.study_id}")
            collections.append(study_collection)
        self._person_set_collections[person_set_collection_id] = \
            PersonSetCollection.combine(collections)


class GenotypeDataStudy(GenotypeData):
    """Represents a singular genotype data study."""

    def __init__(self, config: Box, backend: Any):
        super().__init__(config, [self])

        self._backend = backend
        self._build_person_set_collections()

        self.is_remote = False

    @property
    def study_phenotype(self) -> str:
        return cast(str, self.config.get("study_phenotype", "-"))

    @property
    def is_group(self) -> bool:
        return False

    def get_studies_ids(self, leaves: bool = True) -> list[str]:
        return [self.study_id]

    @property
    def families(self) -> FamiliesData:
        return cast(FamiliesData, self._backend.families)

    def _build_person_set_collection(
        self, person_set_collection_id: str
    ) -> None:
        collection_config = getattr(
            self.config.person_set_collections, person_set_collection_id
        )
        self.person_set_collections[person_set_collection_id] = \
            PersonSetCollection.from_families(collection_config, self.families)
