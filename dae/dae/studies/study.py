"""Classes to represent genotype data."""
from __future__ import annotations

import logging
import os
import time
from abc import ABC, abstractmethod
from collections.abc import Iterable
from dataclasses import dataclass
from os.path import basename, exists
from pathlib import Path
from typing import Any, cast

from box import Box

from dae.common_reports.common_report import CommonReport
from dae.common_reports.denovo_report import DenovoReport
from dae.common_reports.family_report import FamiliesReport
from dae.common_reports.people_counter import PeopleReport
from dae.genotype_storage.genotype_storage_registry import (
    GenotypeStorageRegistry,
)
from dae.pedigrees.families_data import FamiliesData
from dae.person_sets import (
    PersonSetCollection,
    PersonSetCollectionConfig,
    PSCQuery,
    parse_person_set_collections_study_config,
)
from dae.query_variants.base_query_variants import QueryVariantsBase
from dae.query_variants.sql.schema2.sql_query_builder import (
    TagsQuery,
)
from dae.utils.regions import Region
from dae.variants.attributes import Role
from dae.variants.family_variant import FamilyVariant
from dae.variants.variant import SummaryVariant

logger = logging.getLogger(__name__)


@dataclass
class PSCQueryAdjustments:
    """Query adjustments from person set collection query."""

    affected_statues: str | None
    sexes: str | None
    roles: str | None
    person_ids: list[str] | None


class CommonStudyMixin:
    "Mixin class for common study functionality to be reused."

    def __init__(self, config: Box) -> None:
        self._description: str | None = None
        self.config = config

    @property
    def description(self) -> str | None:
        """Load and return description of a genotype data."""
        if self._description is None:
            description_file = self.config["description_file"]
            if basename(description_file) != "description.md" \
               and not exists(description_file):
                # If a non-default description file was given, assert it exists
                raise ValueError(
                    f"missing description file {description_file}")

            if exists(description_file):
                # the default description file may not yet exist
                self._description = Path(description_file).read_text()
        return self._description

    @description.setter
    def description(self, input_text: str) -> None:
        self._description = None
        Path(self.config["description_file"]).write_text(input_text)


class GenotypeData(CommonStudyMixin, ABC):
    """Abstract base class for genotype data."""

    # pylint: disable=too-many-public-methods
    def __init__(
        self, registry: GenotypeStorageRegistry,
        config: Box, studies: list[GenotypeData],
    ):
        super().__init__(config)
        self._registry = registry
        self.studies = studies

        self._description: str | None = None

        self._person_set_collections: dict[str, PersonSetCollection] | None = None  # noqa: E501
        self._parents: set[str] = set()
        self._executor = None
        self.is_remote = False
        self.config_dir: str = self.config["work_dir"]

    def close(self) -> None:
        logger.error("base genotype data close() called for %s", self.study_id)

    @property
    def study_id(self) -> str:
        return cast(str, self.config["id"])

    @property
    def name(self) -> str:
        name = self.config.get("name")
        if name:
            return cast(str, name)
        return self.study_id

    @property
    def year(self) -> str | None:
        return cast(str, self.config.get("year"))

    @property
    def pub_med(self) -> str | None:
        return cast(str, self.config.get("pub_med"))

    @property
    def phenotype(self) -> str | None:
        return cast(str, self.config.get("phenotype"))

    @property
    def has_denovo(self) -> bool:
        return cast(bool, self.config.get("has_denovo"))

    @property
    def has_zygosity(self) -> bool:
        return cast(bool, self.config.get("has_zygosity"))

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
        if self._person_set_collections is None:
            self._person_set_collections = self._build_person_set_collections(
                self.config, self.families,
            )
        return self._person_set_collections

    def add_parent(self, genotype_data_id: str) -> None:
        self._parents.add(genotype_data_id)

    @property
    @abstractmethod
    def is_group(self) -> bool:
        return False

    @abstractmethod
    def get_studies_ids(
        self, *,
        leaves: bool = True,
    ) -> list[str]:
        pass

    @abstractmethod
    def get_children_ids(
        self, *,
        leaves: bool = True,
    ) -> list[str]:
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

    def get_query_leaf_studies(
        self, study_filters: Iterable[str] | None,
    ) -> list[GenotypeDataStudy]:
        """Collect studies contained in local hierarchy."""
        leafs = []
        logger.debug("find leaf studies started...")
        start = time.time()
        if self.is_group:
            leafs = self.get_leaf_children()
        else:
            leafs = [cast(GenotypeDataStudy, self)]
        elapsed = time.time() - start
        logger.debug("leaf studies found in %.2f sec", elapsed)
        logger.debug("leaf children: %s", [st.study_id for st in leafs])
        logger.debug("study_filters: %s", study_filters)

        if study_filters is not None:
            leafs = [st for st in leafs if st.study_id in study_filters]
        logger.debug("studies to query: %s", [st.study_id for st in leafs])
        return leafs

    def query_variants(  # pylint: disable=too-many-locals,too-many-arguments
        self, *,
        regions: list[Region] | None = None,
        genes: list[str] | None = None,
        effect_types: list[str] | None = None,
        family_ids: list[str] | None = None,
        person_ids: list[str] | None = None,
        person_set_collection: PSCQuery | None = None,
        inheritance: str | list[str] | None = None,
        roles: str | None = None,
        sexes: str | None = None,
        affected_statuses: str | None = None,
        variant_type: str | None = None,
        real_attr_filter: list[tuple] | None = None,
        categorical_attr_filter: list[tuple] | None = None,
        ultra_rare: bool | None = None,
        frequency_filter: list[tuple] | None = None,
        return_reference: bool | None = None,
        return_unknown: bool | None = None,
        limit: int | None = None,
        study_filters: list[str] | None = None,
        unique_family_variants: bool = True,
        tags_query: TagsQuery | None = None,
        zygosity_in_status: str | None = None,
    ) -> Iterable[FamilyVariant]:
        """Query and return generator containing variants."""
        if isinstance(inheritance, str):
            inheritance = [inheritance]
        kwargs = {
            "regions": regions,
            "genes": genes,
            "effect_types": effect_types,
            "family_ids": family_ids,
            "person_ids": person_ids,
            "person_set_collection": person_set_collection,
            "inheritance": inheritance,
            "roles": roles,
            "sexes": sexes,
            "affected_statuses": affected_statuses,
            "variant_type": variant_type,
            "real_attr_filter": real_attr_filter,
            "categorical_attr_filter": categorical_attr_filter,
            "ultra_rare": ultra_rare,
            "frequency_filter": frequency_filter,
            "return_reference": return_reference,
            "return_unknown": return_unknown,
            "unique_family_variants": unique_family_variants,
            "limit": limit,
            "study_filters": study_filters,
            "tags_query": tags_query,
            "zygosity_in_status": zygosity_in_status,
        }
        return self._registry.query_variants([
            (st.study_id, kwargs)
            for st in self.get_query_leaf_studies(study_filters)
        ])

    def query_summary_variants(
        self, *,
        regions: list[Region] | None = None,
        genes: list[str] | None = None,
        effect_types: list[str] | None = None,
        variant_type: str | None = None,
        real_attr_filter: list[tuple] | None = None,
        category_attr_filter: list[tuple] | None = None,
        ultra_rare: bool | None = None,
        frequency_filter: list[tuple] | None = None,
        return_reference: bool | None = None,
        return_unknown: bool | None = None,
        limit: int | None = None,
        study_filters: list[str] | None = None,
        **kwargs: Any,
    ) -> Iterable[SummaryVariant]:
        """Query and return generator containing summary variants."""
        # pylint: disable=too-many-locals,too-many-arguments
        kwargs = {
            "regions": regions,
            "genes": genes,
            "effect_types": effect_types,
            "variant_type": variant_type,
            "real_attr_filter": real_attr_filter,
            "category_attr_filter": category_attr_filter,
            "ultra_rare": ultra_rare,
            "frequency_filter": frequency_filter,
            "return_reference": return_reference,
            "return_unknown": return_unknown,
            "limit": limit,
            "study_filters": study_filters,
        }
        return self._registry.query_summary_variants(
            [st.study_id for st in self.get_query_leaf_studies(study_filters)],
            kwargs,
        )

    @property
    @abstractmethod
    def families(self) -> FamiliesData:
        pass

    @abstractmethod
    def _build_person_set_collection(
        self, psc_config: PersonSetCollectionConfig,
        families: FamiliesData,
    ) -> PersonSetCollection:
        pass

    def _build_person_set_collections(
        self, study_config: dict[str, Any] | None,
        families: FamiliesData,
    ) -> dict[str, PersonSetCollection]:
        if study_config is None:
            return {}
        if "person_set_collections" not in study_config:
            return {}

        pscs_config = parse_person_set_collections_study_config(study_config)
        result = {}
        for psc_id, psc_config in pscs_config.items():
            result[psc_id] = self._build_person_set_collection(
                psc_config, families)
        return result

    def get_person_set_collection(
        self, person_set_collection_id: str | None,
    ) -> PersonSetCollection | None:
        if person_set_collection_id is None:
            return None
        return self.person_set_collections.get(person_set_collection_id)

    def build_report(self) -> CommonReport:
        """Generate common report JSON from genotpye data study."""
        config = self.config.get("common_report", {})

        assert config.get("enabled", False), self.study_id

        start = time.time()

        if config.selected_person_set_collections.family_report:
            families_report_collections = [
                self.person_set_collections[collection_id]
                for collection_id in
                config.selected_person_set_collections.family_report
            ]
        else:
            families_report_collections = \
                list(self.person_set_collections.values())

        families_report = FamiliesReport.from_study(
            self,
            families_report_collections,
        )

        people_report = PeopleReport.from_person_set_collections(
            families_report_collections,
        )

        elapsed = time.time() - start
        logger.info(
            "COMMON REPORTS family report build in %.2f sec", elapsed,
        )

        start = time.time()

        if config.selected_person_set_collections.denovo_report:
            denovo_report_collections = [
                self.person_set_collections[collection_id]
                for collection_id in
                config.selected_person_set_collections.denovo_report
            ]
        else:
            denovo_report_collections = \
                list(self.person_set_collections.values())

        denovo_report = DenovoReport.from_genotype_study(
            self,
            denovo_report_collections,
        )
        elapsed = time.time() - start
        logger.info(
            "COMMON REPORTS denovo report build in %.2f sec", elapsed,
        )

        person_sets_config = \
            self.config.get("person_set_collections", {})

        assert person_sets_config.get("selected_person_set_collections") \
            is not None, config

        collection = self.get_person_set_collection(
            person_sets_config.selected_person_set_collections[0],
        )

        phenotype: list[str] = []
        assert collection is not None
        for person_set in collection.person_sets.values():
            if len(person_set.persons) > 0:
                phenotype += person_set.values

        study_type = (
            ",".join(self.study_type)
            if self.study_type
            else None
        )

        number_of_probands = 0
        number_of_siblings = 0
        for family in self.families.values():
            for person in family.members_in_order:
                if not family.member_is_child(person.person_id):
                    continue
                if person.role == Role.prb:
                    number_of_probands += 1
                if person.role == Role.sib:
                    number_of_siblings += 1

        return CommonReport({
            "id": self.study_id,
            "people_report": people_report.to_dict(),
            "families_report": families_report.to_dict(full=True),
            "denovo_report": (
                denovo_report.to_dict()
            ),
            "study_name": self.name,
            "phenotype": phenotype,
            "study_type": study_type,
            "study_year": self.year,
            "pub_med": self.pub_med,
            "families": len(self.families.values()),
            "number_of_probands": number_of_probands,
            "number_of_siblings": number_of_siblings,
            "denovo": self.has_denovo,
            "transmitted": self.has_transmitted,
            "study_description": self.description,
        })

    def build_and_save(
        self,
        *,
        force: bool = False,
    ) -> CommonReport | None:
        """Build a common report for a study, saves it and returns the report.

        If the common reports are disabled for the study, the function skips
        building the report and returns None.

        If the report already exists the default behavior is to skip building
        the report. You can force building the report by
        passing `force=True` to the function.
        """
        common_report_config = self.config.get("common_report", {})
        if not common_report_config.get("enabled"):
            return None
        report_filename = common_report_config.get("file_path")
        try:
            if os.path.exists(report_filename) and not force:
                logger.info(
                    "common report for %s already exists, loading it",
                    self.study_id)
                return CommonReport.load(report_filename)
        except Exception:  # noqa: BLE001
            logger.warning(
                "unable to load common report for %s", self.study_id,
                exc_info=True)
        report = self.build_report()
        report.save(report_filename)
        return report

    def get_common_report(self) -> CommonReport | None:
        """Return a study's common report."""
        common_report_config = self.config.get("common_report", {})
        if not common_report_config.get("enabled"):
            return None

        report = CommonReport.load(common_report_config.get("file_path"))
        if report is None:
            report = self.build_and_save()
        return report


class GenotypeDataGroup(GenotypeData):
    """
    Represents a group of genotype data classes.

    Queries to this object will be sent to all child data.
    """

    def __init__(
        self, registry: GenotypeStorageRegistry, config: Box,
        studies: Iterable[GenotypeData],
    ):
        super().__init__(
            registry, config, list(studies),
        )
        self._families: FamiliesData
        self.rebuild_families()

        self._executor = None
        self.is_remote = False
        for study in self.studies:
            study.add_parent(self.study_id)

    @property
    def is_group(self) -> bool:
        return True

    @property
    def has_denovo(self) -> bool:
        has_denovo = cast(bool, self.config.get("has_denovo"))
        return has_denovo or any(
            study.has_denovo for study in self.studies
        )

    @property
    def has_transmitted(self) -> bool:
        has_transmitted = cast(bool, self.config.get("has_transmitted"))
        return has_transmitted or any(
            study.has_transmitted for study in self.studies
        )

    @property
    def families(self) -> FamiliesData:
        return self._families

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

    def get_children_ids(
        self, *,
        leaves: bool = True,
    ) -> list[str]:
        result = []
        for study in self.studies:
            if leaves:
                result.extend([
                    child_id
                    for child_id in study.get_children_ids(leaves=True)
                    if child_id not in result
                ])
            else:
                result.append(study.study_id)
        return result

    def rebuild_families(self) -> None:
        """Construct genotype group families data from child studies."""
        logger.info(
            "building combined families from studies: %s",
            [st.study_id for st in self.studies])

        if len(self.studies) == 1:
            self._families = self.studies[0].families
            self._person_set_collections = self._build_person_set_collections(
                self.config,
                self._families,
            )
            return

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
        self._families = result

        pscs = self._build_person_set_collections(
            self.config,
            result,
        )

        self._person_set_collections = pscs

    def _build_person_set_collection(
        self, psc_config: PersonSetCollectionConfig,
        families: FamiliesData,
    ) -> PersonSetCollection:

        psc_id = psc_config.id

        studies_psc = []
        for study in self.studies:
            study_psc = study.get_person_set_collection(psc_id)
            if study_psc is None:
                raise ValueError(
                    f"person set collection {psc_id} "
                    f"not found in study {study.study_id}")
            studies_psc.append(study_psc)

        psc = PersonSetCollection.combine(studies_psc, families)
        for fpid, person in families.real_persons.items():
            person_set_value = psc.get_person_set_of_person(fpid)
            assert person_set_value is not None
            person.set_attr(psc_id, person_set_value.id)
        return psc


class GenotypeDataStudy(GenotypeData):
    """Represents a singular genotype data study."""

    def __init__(self, registry: GenotypeStorageRegistry, config: Box):
        super().__init__(registry, config, [self])
        self._registry = registry
        self.is_remote = False

    @property
    def backend(self) -> QueryVariantsBase:
        storage = self._registry.find_storage(self.study_id)
        return storage.loaded_variants[self.study_id]

    @property
    def study_phenotype(self) -> str:
        return cast(str, self.config.get("study_phenotype", "-"))

    @property
    def is_group(self) -> bool:
        return False

    def get_studies_ids(
        self, *,
        leaves: bool = True,  # noqa: ARG002
    ) -> list[str]:
        return [self.study_id]

    def get_children_ids(
        self, *,
        leaves: bool = True,  # noqa: ARG002
    ) -> list[str]:
        return [self.study_id]

    @property
    def families(self) -> FamiliesData:
        return self.backend.families

    def _build_person_set_collection(
        self, psc_config: PersonSetCollectionConfig,
        families: FamiliesData,
    ) -> PersonSetCollection:

        psc = PersonSetCollection.from_families(psc_config, self.families)

        for fpid, person in families.real_persons.items():
            person_set_value = psc.get_person_set_of_person(fpid)
            assert person_set_value is not None
            person.set_attr(psc.id, person_set_value.id)
        return psc
