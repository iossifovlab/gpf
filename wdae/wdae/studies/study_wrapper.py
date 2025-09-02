from __future__ import annotations

import contextlib
import itertools
import logging
import time
from abc import abstractmethod
from collections.abc import Callable, Generator, Iterable, Iterator
from copy import copy
from typing import Any, Protocol, cast

from box import Box
from dae.configuration.gpf_config_parser import GPFConfigParser
from dae.configuration.schemas.wdae_study_config import (
    wdae_study_config_schema,
)
from dae.enrichment_tool.enrichment_utils import (
    get_enrichment_cache_path,
    get_enrichment_config,
)
from dae.genotype_storage.genotype_storage_registry import (
    GenotypeStorageRegistry,
)
from dae.pedigrees.families_data import FamiliesData
from dae.person_sets import PersonSetCollection
from dae.person_sets.person_sets import PSCQuery
from dae.pheno.common import MeasureType
from dae.pheno.pheno_data import Measure, PhenotypeData
from dae.studies.study import GenotypeData
from dae.utils.dae_utils import join_line
from dae.variants.attributes import Role
from dae.variants.family_variant import FamilyVariant
from dae.variants.variant import SummaryVariant

logger = logging.getLogger(__name__)


class QueryTransformerProtocol(Protocol):
    """Protocol for query transformer interface."""

    @abstractmethod
    def transform_kwargs(
        self, study: WDAEAbstractStudy, **kwargs: Any,
    ) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def extract_person_set_collection_query(
            self, study: WDAEAbstractStudy, kwargs: dict[str, Any],
    ) -> PSCQuery:
        raise NotImplementedError

    @abstractmethod
    def get_unique_family_variants(self, kwargs: dict[str, Any]) -> bool:
        raise NotImplementedError


class ResponseTransformerProtocol(Protocol):
    """Protocol for response transformer interface."""

    @abstractmethod
    def variant_transformer(
        self, study: WDAEStudy,
        pheno_values: dict[str, Any] | None,
    ) -> Callable[[FamilyVariant], FamilyVariant]:
        raise NotImplementedError

    @abstractmethod
    def transform_gene_view_summary_variant_download(
        self,
        variants: Iterable[SummaryVariant],
        frequency_column: str,
        summary_variant_ids: set[str],
    ) -> Iterator[str]:
        """Produce an iterator for a download file response."""
        raise NotImplementedError

    @abstractmethod
    def transform_gene_view_summary_variant(
        self, variant: SummaryVariant, frequency_column: str,
    ) -> Generator[dict[str, Any], None, None]:
        raise NotImplementedError

    @abstractmethod
    def build_variant_row(
        self, study: WDAEAbstractStudy,
        v: SummaryVariant | FamilyVariant,
        column_descs: list[dict], **kwargs: str | None,
    ) -> list:
        raise NotImplementedError


def get_clean_config(config: dict[str, Any]) -> dict[str, Any]:
    config.pop("parents", None)
    return remove_none_values(config)


def remove_none_values(config: dict[str, Any]) -> dict[str, Any]:
    """Remove None values from config"""
    new_config = {}
    for k, v in config.items():
        if isinstance(v, dict):
            inner = remove_none_values(v)
            if len(inner.keys()) > 0:
                new_config[k] = inner
        elif v is not None:
            new_config[k] = v
    return new_config


class WDAEAbstractStudy:
    """A genotype and phenotype data wrapper for use in the wdae module."""

    def __init__(
        self,
        genotype_data: GenotypeData | None = None,
        phenotype_data: PhenotypeData | None = None,
    ):
        if genotype_data is None and phenotype_data is None:
            raise ValueError("Cannot create study without providing data!")
        self._genotype_data = genotype_data
        self._phenotype_data = phenotype_data
        self._config: dict[str, Any] = self.make_config(
            self._genotype_data, self._phenotype_data)
        self._init_genotype_browser()

    @property  # Remove when all external references are removed
    def config(self) -> dict[str, Any]:
        return self._config

    @property  # Remove when all external references are removed
    def genotype_data(self) -> GenotypeData:
        if self._genotype_data is None:
            raise ValueError
        return self._genotype_data

    @property  # Remove when all external references are removed
    def phenotype_data(self) -> PhenotypeData:
        if self._phenotype_data is None:
            raise ValueError
        return self._phenotype_data

    @property
    def is_genotype(self) -> bool:
        return self._genotype_data is not None

    @property
    def is_phenotype(self) -> bool:
        return self._genotype_data is None \
               and self._phenotype_data is not None

    @property
    def has_pheno_data(self) -> bool:
        return self._phenotype_data is not None

    @property
    def has_genotype_data(self) -> bool:
        return cast(bool, self._config["has_genotype"])

    @property
    def study_id(self) -> str:
        if self.is_phenotype:
            return self.phenotype_data.pheno_id
        return self.genotype_data.study_id

    @property
    def name(self) -> str:
        if self.is_phenotype:
            return cast(str, self.phenotype_data.name)
        return self.genotype_data.name

    @property
    @abstractmethod
    def description(self) -> str | None:
        pass

    @description.setter
    @abstractmethod
    def description(self, input_text: str) -> None:
        pass

    @property
    def is_group(self) -> bool:
        if self.is_phenotype:
            return self.phenotype_data.is_group
        return self.genotype_data.is_group

    @property
    def parents(self) -> set[str]:
        if self.is_phenotype:
            return self.phenotype_data.parents
        return self.genotype_data.parents

    @property
    def families(self) -> FamiliesData:
        if self.is_phenotype:
            return self.phenotype_data.families
        return self.genotype_data.families

    def get_children_ids(self, *, leaves: bool = True) -> list[str]:
        """Return the list of children ids."""
        if self.is_phenotype:
            return self.phenotype_data.get_children_ids(leaves=leaves)
        return self.genotype_data.get_children_ids(leaves=leaves)

    def get_studies_ids(self, *, leaves: bool = True) -> list[str]:
        """Return the list of children ids."""
        if self.is_phenotype:
            return self.phenotype_data.get_children_ids(leaves=leaves)
        return self.genotype_data.get_studies_ids(leaves=leaves)

    @abstractmethod
    def get_measures_json(
        self,
        used_types: list[str],
    ) -> list[dict[str, Any]]:
        """Get list of measures in json format"""

    @property
    def config_columns(self) -> dict[str, Any] | None:
        if not self.config["genotype_browser"]["enabled"]:
            return None
        return cast(dict, self.config["genotype_browser"]["columns"])

    @property
    def person_set_collections(self) -> dict[str, PersonSetCollection]:
        # later
        return self.genotype_data.person_set_collections

    @staticmethod
    def make_config(
        genotype_data: GenotypeData | None,
        phenotype_data: PhenotypeData | None,
    ) -> dict[str, Any]:
        """Create a configuration for the WDAEStudy."""
        config: dict[str, Any] = {}
        if genotype_data:
            if isinstance(genotype_data.config, Box):
                config = genotype_data.config.to_dict()
            else:
                config = cast(dict[str, Any], genotype_data.config.to_dict())
        elif phenotype_data:
            config["id"] = phenotype_data.pheno_id
            config["name"] = phenotype_data.name
            config["phenotype_data"] = phenotype_data.pheno_id
            config["study_type"] = ["Phenotype study"]
            config["enabled"] = True
            config["studies"] = phenotype_data.get_children_ids(leaves=False)
            config["phenotype_browser"] = True
            config["gene_browser"] = {"enabled": False}
            config["genotype_browser"] = {"enabled": False}
            config["enrichment"] = {"enabled": False}
            config["denovo_gene_sets"] = {"enabled": False}
            config["phenotype_tool"] = False
            config["has_present_in_child"] = False
            config["has_present_in_parent"] = False
            config["has_denovo"] = False
            config["has_zygosity"] = False
            config["has_transmitted"] = False
            config["has_genotype"] = False
            config["common_report"] = phenotype_data.config.get(
                "common_report",
                {"enabled": False},
            )
            config["description_editable"] = \
                phenotype_data.config["description_editable"]
        return GPFConfigParser.process_config_raw(
            get_clean_config(config),
            wdae_study_config_schema,
        )

    @property
    def enrichment_config(self) -> Box | None:
        """Return the enrichment configuration for the study."""
        if self.is_phenotype:
            return None
        config = get_enrichment_config(self.genotype_data)
        if config is None:
            return None
        return config

    @property
    def enrichment_cache_path(self) -> str | None:
        """Return the enrichment configuration for the study."""
        if self.is_phenotype:
            return None
        return get_enrichment_cache_path(self.genotype_data)

    def _init_genotype_browser(self) -> None:
        if not self.is_genotype or \
                not self.genotype_data.config["genotype_browser"]:
            return

        genotype_browser_config = \
            self.genotype_data.config.get("genotype_browser", {})

        # PERSON AND FAMILY FILTERS
        self.person_filters = \
            genotype_browser_config.get("person_filters") or None
        self.family_filters = \
            genotype_browser_config.get("family_filters") or None

        # GENE SCORES
        if genotype_browser_config["column_groups"] and \
                "gene_scores" in genotype_browser_config["column_groups"]:
            self.gene_score_column_sources = [
                genotype_browser_config["columns"]["genotype"][slot]["source"]
                for slot in (
                    genotype_browser_config[
                        "column_groups"]["gene_scores"]["columns"]
                    or []
                )
            ]
        else:
            self.gene_score_column_sources = []

        # PREVIEW AND DOWNLOAD COLUMNS
        self.columns = genotype_browser_config["columns"]
        self.column_groups = genotype_browser_config["column_groups"]
        self._validate_column_groups()
        self.preview_columns = genotype_browser_config["preview_columns"]
        if genotype_browser_config.get("preview_columns_ext"):
            self.preview_columns.extend(
                genotype_browser_config["preview_columns_ext"])
        self.download_columns = genotype_browser_config["download_columns"]
        if genotype_browser_config.get("download_columns_ext"):
            self.download_columns.extend(
                genotype_browser_config["download_columns_ext"])

        self.summary_preview_columns = \
            genotype_browser_config["summary_preview_columns"]
        self.summary_download_columns = \
            genotype_browser_config["summary_download_columns"]

    def get_person_set_collection(
        self, collection_id: str | None,
    ) -> PersonSetCollection | None:
        if self.is_phenotype:
            return None
        return self.genotype_data.get_person_set_collection(collection_id)

    def _validate_column_groups(self) -> bool:
        genotype_cols = self.columns.get("genotype") or []
        phenotype_cols = self.columns.get("phenotype") or []
        for column_group_name, column_group in self.column_groups.items():
            if column_group is None:
                logger.warning(
                    "bad configuration for column group %s",
                    column_group_name)
                continue
            for column_id in column_group["columns"]:
                if column_id not in genotype_cols \
                   and column_id not in phenotype_cols:
                    logger.warning(
                        "column %s not defined in configuration", column_id)
                    return False
        return True

    @abstractmethod
    def query_variants_wdae(
        self, kwargs: dict[str, Any],
        sources: list[dict[str, Any]],
        query_transformer: QueryTransformerProtocol,
        response_transformer: ResponseTransformerProtocol,
        *,
        max_variants_count: int | None = 10000,
        max_variants_message: bool = False,
    ) -> Generator[list | None, None, None]:
        """Wrap query variants method for WDAE streaming."""

    @abstractmethod
    def query_variants_preview_wdae(
        self, kwargs: dict[str, Any],
        query_transformer: QueryTransformerProtocol,
        response_transformer: ResponseTransformerProtocol,
        *,
        max_variants_count: int | None = 10000,
    ) -> Generator[list | None, None, None]:
        """Wrap query variants method for WDAE streaming as preview."""

    @abstractmethod
    def query_variants_download_wdae(
        self, kwargs: dict[str, Any],
        query_transformer: QueryTransformerProtocol,
        response_transformer: ResponseTransformerProtocol,
        *,
        max_variants_count: int | None = 10000,
    ) -> Generator[list | None, None, None]:
        """Wrap query variants method for WDAE streaming as download."""

    def get_measures(
        self,
        instrument_name: str | None = None,
        measure_type: MeasureType | None = None,
    ) -> dict[str, Measure]:
        return self.phenotype_data.get_measures(instrument_name, measure_type)

    @abstractmethod
    def get_gene_view_summary_variants(
        self, frequency_column: str,
        query_transformer: QueryTransformerProtocol,
        response_transformer: ResponseTransformerProtocol,
        **kwargs: Any,
    ) -> Generator[dict[str, Any], None, None]:
        """Return gene browser summary variants."""

    @abstractmethod
    def get_gene_view_summary_variants_download(
        self, frequency_column: str,
        query_transformer: QueryTransformerProtocol,
        response_transformer: ResponseTransformerProtocol,
        **kwargs: Any,
    ) -> Iterable:
        """Return gene browser summary variants for downloading."""


class WDAEStudy(WDAEAbstractStudy):
    """A genotype and phenotype data wrapper for use in the wdae module."""

    def __init__(
        self,
        genotype_storage_registry: GenotypeStorageRegistry,
        genotype_data: GenotypeData | None,
        phenotype_data: PhenotypeData | None,
        query_transformer: QueryTransformerProtocol | None = None,
        response_transformer: ResponseTransformerProtocol | None = None,
    ) -> None:
        self.children = [self]
        self.query_transformer = query_transformer
        self.response_transformer = response_transformer
        self.registry = genotype_storage_registry
        super().__init__(genotype_data, phenotype_data)
        self._pheno_values_cache = self._get_all_pheno_values()
        self.is_remote = False

    def _get_all_pheno_values(self) -> dict | None:
        if not self.has_pheno_data \
           or not self.config_columns \
           or not self.config_columns.get("phenotype"):
            return None

        pheno_values = {}

        for column in self.config_columns["phenotype"].values():
            assert column.get("role") is not None
            result = {}
            column_values_iter = self.phenotype_data.get_people_measure_values(
                [column.get("source")],
                roles=[Role.from_name(column.get("role"))],
            )
            for column_value in column_values_iter:
                result[column_value["family_id"]] = \
                    column_value[column.get("source")]

            pheno_column_name = f"{column.get('source')}.{column.get('role')}"
            pheno_values[pheno_column_name] = result
        return pheno_values

    @property
    def description(self) -> str | None:
        if self.is_phenotype:
            return self.phenotype_data.description
        return self.genotype_data.description

    @description.setter
    def description(self, input_text: str) -> None:
        if self.is_phenotype:
            self.phenotype_data.description = input_text
        else:
            self.genotype_data.description = input_text

    @staticmethod
    def get_columns_as_sources(
        config: dict[str, Any], column_ids: list[str],
    ) -> list[dict[str, Any]]:
        """Return the list of column sources."""
        column_groups = config["genotype_browser"]["column_groups"]
        genotype_cols = config["genotype_browser"]["columns"] \
            .get("genotype", {})
        if genotype_cols is None:
            genotype_cols = {}
        phenotype_cols = config["genotype_browser"]["columns"] \
            .get("phenotype", {})
        if phenotype_cols is None:
            phenotype_cols = {}
        result = []

        for column_id in column_ids:
            if column_id in column_groups:
                source_cols = column_groups[column_id]["columns"]
            else:
                source_cols = [column_id]

            for source_col_id in source_cols:
                if source_col_id in genotype_cols:
                    result.append(dict(genotype_cols[source_col_id]))
                elif source_col_id in phenotype_cols:
                    result.append(dict(phenotype_cols[source_col_id]))

        return result

    @staticmethod
    def build_genotype_data_all_datasets(
        genotype_data: GenotypeData,
    ) -> dict[str, Any]:
        """Prepare response for all genotype datasets."""
        config = genotype_data.config.to_dict()
        keys = [
            "id",
            "name",
            "has_denovo",
            "has_zygosity",
            "phenotype_data",
            "has_transmitted",
        ]
        result = {
            key: config.get(key, None) for key in keys
        }
        result["has_denovo"] = genotype_data.has_denovo
        result["has_transmitted"] = genotype_data.has_transmitted
        result["name"] = result["name"] or result["id"]
        result["genotype_browser"] = \
            config.get("genotype_browser", {}).get("enabled")
        result["common_report"] = {
            "enabled": config.get("common_report", {}).get("enabled"),
        }
        result["enrichment_tool"] = \
            config.get("enrichment", {}).get("enabled") or result["has_denovo"]
        result["gene_browser"] = config.get("gene_browser")
        result["phenotype_browser"] = config.get(
            "phenotype_browser",
            result["phenotype_data"] is not None,
        )
        result["phenotype_tool"] = config.get(
            "phenotype_tool",
            result["phenotype_data"] is not None
            and result["has_denovo"] is True,
        )
        return result

    @staticmethod
    def build_genotype_data_description(
        gpf_instance: Any,
        genotype_data: GenotypeData,
        person_set_collection_configs: dict[str, Any] | None,
    ) -> dict[str, Any]:
        """Build and return genotype data group description."""
        config = genotype_data.config.to_dict()
        keys = [
            "id",
            "name",
            "phenotype_data",
            "study_type",
            "studies",
            "has_present_in_child",
            "has_present_in_parent",
            "has_zygosity",
            "gene_browser",
            "description_editable",
        ]
        result = {
            key: config.get(key, None) for key in keys
        }
        result["has_denovo"] = genotype_data.has_denovo
        result["has_transmitted"] = genotype_data.has_transmitted
        result["genotype_browser"] = config["genotype_browser"]["enabled"]
        result["phenotype_browser"] = config.get(
            "phenotype_browser",
            result["phenotype_data"] is not None,
        )
        result["phenotype_tool"] = config.get(
            "phenotype_tool",
            result["phenotype_data"] is not None
            and result["has_denovo"] is True,
        )
        result["genotype_browser_config"] = {
            key: config["genotype_browser"].get(key, None) for key in [
                "has_family_filters",
                "has_family_pheno_filters",
                "has_person_filters",
                "has_person_pheno_filters",
                "has_study_filters",
                "has_present_in_child",
                "has_present_in_parent",
                "has_pedigree_selector",
                "variant_types",
                "selected_variant_types",
                "max_variants_count",
                "person_filters",
                "family_filters",
                "genotype",
                "inheritance_type_filter",
                "selected_inheritance_type_filter_values",
            ]
        }

        if result["phenotype_data"] is not None \
            and config["genotype_browser"].get(
                "has_family_structure_filter", None) is None \
            and result["genotype_browser_config"]["has_family_pheno_filters"] \
                is None:
            result["genotype_browser_config"][
                "has_family_pheno_filters"] = True

        if result["phenotype_data"] is not None \
            and config["genotype_browser"].get(
                "has_person_structure_filter", None) is None \
            and result["genotype_browser_config"]["has_person_pheno_filters"] \
                is None:
            result["genotype_browser_config"][
                "has_person_pheno_filters"] = True

        table_columns = []
        for column in config["genotype_browser"]["preview_columns"]:
            logger.info(
                "processing preview column %s for study %s",
                column,
                config["id"],
            )

            if column in config["genotype_browser"]["column_groups"]:
                new_col = dict(
                    config["genotype_browser"]["column_groups"][column],
                )
                new_col["columns"] = WDAEStudy.get_columns_as_sources(
                    config, [column],
                )
                table_columns.append(new_col)
            else:
                if config["genotype_browser"]["columns"]["genotype"] and \
                        column in \
                        config["genotype_browser"]["columns"]["genotype"]:
                    table_columns.append(
                        dict(
                            config
                            ["genotype_browser"]["columns"]
                            ["genotype"][column],
                        ),
                    )
                elif config["genotype_browser"]["columns"]["phenotype"] \
                    and column in \
                        config["genotype_browser"]["columns"]["phenotype"]:
                    table_columns.append(
                        dict(
                            config
                            ["genotype_browser"]["columns"]
                            ["phenotype"][column]),
                    )
                else:
                    raise KeyError(f"No such column {column} configured!")
        result["genotype_browser_config"]["table_columns"] = table_columns

        result["study_types"] = result["study_type"]
        result["enrichment_tool"] = \
            config["enrichment"]["enabled"] or result["has_denovo"]
        result["common_report"] = config["common_report"]
        result["common_report"].pop("file_path", None)
        result["person_set_collections"] = person_set_collection_configs
        result["name"] = result["name"] or result["id"]

        result["enrichment"] = config["enrichment"]
        if "background" in result["enrichment"]:
            if "coding_len_background_model" in \
                    result["enrichment"]["background"]:
                result["enrichment"]["background"][
                    "coding_len_background_model"].pop("file", None)
            if "samocha_background_model" in \
                    result["enrichment"]["background"]:
                result["enrichment"]["background"][
                    "samocha_background_model"].pop("file", None)

        result["study_names"] = None
        if result["studies"] is not None:
            logger.debug("found studies in %s", config["id"])
            study_names = []
            for study_id in result["studies"]:
                wrapper = gpf_instance.get_wdae_wrapper(study_id)
                if wrapper is None:
                    logger.warning(
                        "no wrapper found for study %s", study_id)
                    continue
                name = (
                    wrapper.config.get("name")
                    if wrapper.config.get("name") is not None
                    else wrapper.config.get("id")
                )
                study_names.append(name)
                result["study_names"] = study_names

        return result

    def get_measures_json(
        self,
        used_types: list[str],
    ) -> list[dict[str, Any]]:
        measures = list(self.get_measures().values())
        measures = [m for m in measures if m.measure_type.name in used_types]

        return [m.to_json() for m in measures]

    def _extract_pre_kwargs(
            self, query_transformer: QueryTransformerProtocol,
            kwargs: dict[str, Any],
    ) -> dict[str, Any]:
        pre_kwargs = {
            "personFilters": kwargs.pop("personFilters", None),
            "familyFilters": kwargs.pop("familyFilters", None),
            "personFiltersBeta": kwargs.pop("personFiltersBeta", None),
            "familyPhenoFilters": kwargs.pop("familyPhenoFilters", None),
            "personIds": kwargs.pop("personIds", None),
            "familyIds": kwargs.pop("familyIds", None),
        }
        pre_kwargs = {
            k: v for k, v in pre_kwargs.items() if v is not None
        }
        pre_kwargs = query_transformer.transform_kwargs(
            self, **pre_kwargs,
        )
        for key in ["person_ids", "family_ids"]:
            if pre_kwargs.get(key) is not None:
                kwargs[key] = pre_kwargs[key]
        return kwargs

    def query_variants_raw(
        self, kwargs: dict[str, Any],
        query_transformer: QueryTransformerProtocol,
        *,
        max_variants_count: int | None = 10000,
        max_variants_message: bool = False,  # noqa: ARG002
    ) -> Iterator[FamilyVariant]:
        """Query for raw family variants from registry."""

        kwargs = self._extract_pre_kwargs(query_transformer, kwargs)
        children_kwargs = []
        for child_id in self.get_children_ids(leaves=True):
            child = None
            if child_id == self.study_id:
                child = self
            else:
                for ch in self.children:
                    if ch.study_id == child_id:
                        child = ch
                        break
            if child is None:
                raise ValueError(
                    f"Child study {child_id} of {self.study_id} "
                    f"not found in {self.children}!",
                )
            try:
                child_kwargs = query_transformer.transform_kwargs(
                    child, **kwargs)
                children_kwargs.append((child_id, child_kwargs))
            except ValueError:
                logger.warning(
                    "Could not transform kwargs for child %s of study %s",
                    child_id, self.study_id,
                )
        kwargs = query_transformer.transform_kwargs(self, **kwargs)

        limit = kwargs.get("limit", max_variants_count)

        started = time.time()
        index = 0
        logger.debug(
            "study wrapper (%s) creating query_result_variants...",
            self.name)
        try:
            variants = enumerate(filter(None, self.registry.query_variants(
                children_kwargs, limit,
            )))

            for idx, variant in variants:
                index = idx
                yield variant
        except GeneratorExit:
            pass
        finally:
            elapsed = time.time() - started
            logger.info(
                "study wrapper (%s)  query returned %s variants; "
                "closed in %0.3fsec", self.study_id, index, elapsed)

    def query_variants_wdae(
        self, kwargs: dict[str, Any],
        sources: list[dict[str, Any]],
        query_transformer: QueryTransformerProtocol,
        response_transformer: ResponseTransformerProtocol,
        *,
        max_variants_count: int | None = 10000,
        max_variants_message: bool = False,
    ) -> Generator[list | None, None, None]:
        """Wrap query variants method for WDAE streaming of variants."""
        # pylint: disable=too-many-locals,too-many-branches

        transform = response_transformer.variant_transformer(
            self, self._pheno_values_cache,
        )

        logger.debug(
            "study wrapper (%s) creating query_variants_wdae...",
            self.name)
        try:
            variants = self.query_variants_raw(
                kwargs, query_transformer,
                max_variants_count=max_variants_count,
                max_variants_message=max_variants_message,
            )
            psc_query = query_transformer.extract_person_set_collection_query(
                self, copy(kwargs))

            for variant in variants:
                v = transform(variant)

                row_variant = response_transformer.build_variant_row(
                    self,
                    v, sources,
                    person_set_collection=psc_query.psc_id if psc_query
                    else None)

                yield row_variant
        except GeneratorExit:
            pass

    def query_variants_preview_wdae(
        self, kwargs: dict[str, Any],
        query_transformer: QueryTransformerProtocol,
        response_transformer: ResponseTransformerProtocol,
        *,
        max_variants_count: int | None = 10000,
    ) -> Generator[list | None, None, None]:
        cols = self.genotype_data.config["genotype_browser"]["preview_columns"]
        sources = WDAEStudy.get_columns_as_sources(
            self.genotype_data.config, cols,
        )
        yield from self.query_variants_wdae(
            kwargs,
            sources,
            query_transformer,
            response_transformer,
            max_variants_count=max_variants_count,
            max_variants_message=True,
        )

    def query_variants_download_wdae(
        self, kwargs: dict[str, Any],
        query_transformer: QueryTransformerProtocol,
        response_transformer: ResponseTransformerProtocol,
        *,
        max_variants_count: int | None = 10000,
    ) -> Generator[list | None, None, None]:
        cols = self.genotype_data.config["genotype_browser"]["download_columns"]
        sources = WDAEStudy.get_columns_as_sources(
            self.genotype_data.config, cols,
        )

        result = self.query_variants_wdae(
            kwargs,
            sources,
            query_transformer,
            response_transformer,
            max_variants_count=max_variants_count,
            max_variants_message=True,
        )

        columns = [s.get("name", s["source"]) for s in sources]

        yield from map(
            join_line, itertools.chain([columns], filter(None, result)))  # type: ignore

    def _query_gene_view_summary_variants(
        self, query_transformer: QueryTransformerProtocol, **kwargs: Any,
    ) -> Generator[SummaryVariant, None, None]:

        kwargs = self._extract_pre_kwargs(query_transformer, kwargs)

        query_kwargs = query_transformer.transform_kwargs(
            self, **kwargs,
        )

        variants = self.registry.query_summary_variants(
            self.get_children_ids(leaves=True), query_kwargs,
        )

        yield from variants

    def get_gene_view_summary_variants(
        self, frequency_column: str,
        query_transformer: QueryTransformerProtocol,
        response_transformer: ResponseTransformerProtocol,
        **kwargs: Any,
    ) -> Generator[dict[str, Any], None, None]:
        """Return gene browser summary variants."""
        variants = self._query_gene_view_summary_variants(
            query_transformer, **kwargs,
        )

        for variant in variants:
            yield from response_transformer.\
                transform_gene_view_summary_variant(variant, frequency_column)

    def get_gene_view_summary_variants_download(
        self, frequency_column: str,
        query_transformer: QueryTransformerProtocol,
        response_transformer: ResponseTransformerProtocol,
        **kwargs: Any,
    ) -> Iterable:
        """Return gene browser summary variants for downloading."""
        summary_variant_ids = kwargs.pop("summaryVariantIds", None)

        variants = self._query_gene_view_summary_variants(
            query_transformer, **kwargs,
        )

        return response_transformer.\
            transform_gene_view_summary_variant_download(
                variants, frequency_column, summary_variant_ids,
            )


class WDAEStudyGroup(WDAEStudy):
    """Genotype data study wrapper class for WDAE."""

    def __init__(
        self,
        genotype_storage_registry: GenotypeStorageRegistry,
        genotype_data: GenotypeData | None,
        pheno_data: PhenotypeData | None,
        children: list[WDAEStudy],
        *,
        query_transformer: QueryTransformerProtocol | None = None,
        response_transformer: ResponseTransformerProtocol | None = None,
    ) -> None:
        super().__init__(
            genotype_storage_registry,
            genotype_data, pheno_data,
            query_transformer=query_transformer,
            response_transformer=response_transformer,
        )
        self.children = children

    def get_studies_ids(self, *, leaves: bool = True) -> list[str]:
        if self.is_phenotype:
            return self.phenotype_data.get_children_ids(leaves=leaves)
        return self.genotype_data.get_studies_ids(leaves=leaves)

    def get_children_ids(self, *, leaves: bool = True) -> list[str]:
        """Return the list of children ids."""
        if self.is_phenotype:
            children = self.phenotype_data.get_children_ids(leaves=leaves)
        else:
            children = self.genotype_data.get_children_ids(leaves=leaves)

        return list(
            filter(lambda child_id: child_id != self.study_id, children))
