from __future__ import annotations

import logging
import time
from abc import abstractmethod
from collections.abc import Callable, Generator, Iterable, Iterator
from contextlib import closing
from typing import Any, Protocol, cast

from box import Box

from dae.pedigrees.families_data import FamiliesData
from dae.person_sets import PersonSetCollection
from dae.person_sets.person_sets import PSCQuery
from dae.pheno.pheno_data import PhenotypeData
from dae.query_variants.query_runners import QueryResult, QueryRunner
from dae.studies.study import GenotypeData
from dae.variants.attributes import Role
from dae.variants.family_variant import FamilyAllele, FamilyVariant
from dae.variants.variant import SummaryVariant

logger = logging.getLogger(__name__)


class QueryTransformerProtocol(Protocol):
    """Protocol for query transformer interface."""

    @abstractmethod
    def transform_kwargs(
        self, study_wrapper: StudyWrapper, **kwargs: Any,
    ) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def extract_person_set_collection_query(
            self, study_wrapper: StudyWrapper, kwargs: dict[str, Any],
    ) -> PSCQuery:
        raise NotImplementedError


class ResponseTransformerProtocol(Protocol):
    """Protocol for response transformer interface."""

    @abstractmethod
    def variant_transformer(
        self, study_wrapper: StudyWrapper,
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
        self, study_wrapper: StudyWrapper,
        v: SummaryVariant | FamilyVariant,
        column_descs: list[dict], **kwargs: str | None,
    ) -> list:
        raise NotImplementedError


class WDAEStudy:
    """A genotype and phenotype data wrapper for use in the wdae module."""

    def __init__(
        self,
        genotype_data: GenotypeData | None = None,
        phenotype_data: PhenotypeData | None = None,
    ):
        if genotype_data is None and phenotype_data is None:
            raise ValueError("Cannot create wrapper without providing data!")
        self._genotype_data = genotype_data
        self._phenotype_data = phenotype_data

    @property
    def genotype_data(self) -> GenotypeData:
        if self._genotype_data is None:
            raise ValueError
        return self._genotype_data

    @property
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
    def study_id(self) -> str:
        if self.is_phenotype:
            return self.phenotype_data.pheno_id
        return self.genotype_data.study_id

    @property
    def name(self) -> str:
        if self.is_phenotype:
            return self.phenotype_data.name
        return self.genotype_data.name

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

    def get_children_ids(self, *, leaves=True) -> list[str]:
        if self.is_phenotype:
            return self.phenotype_data.get_children_ids(leaves=leaves)
        return self.genotype_data.get_studies_ids(leaves=leaves)


class StudyWrapperBase(WDAEStudy):
    """Defines WDAE wrapper class to DAE genotype data object."""

    def __init__(
        self, genotype_data: GenotypeData, phenotype_data: PhenotypeData | None,
    ):
        super().__init__(genotype_data, phenotype_data)
        self.config = self.genotype_data.config
        assert self.config is not None, self.genotype_data.study_id

    @staticmethod
    def get_columns_as_sources(
        config: Box, column_ids: list[str],
    ) -> list[dict[str, Any]]:
        """Return the list of column sources."""
        column_groups = config.genotype_browser.column_groups
        genotype_cols = config.genotype_browser.columns.get("genotype", {})
        if genotype_cols is None:
            genotype_cols = {}
        phenotype_cols = config.genotype_browser.columns.get("phenotype", {})
        if phenotype_cols is None:
            phenotype_cols = {}
        result = []

        for column_id in column_ids:
            if column_id in column_groups:
                source_cols = column_groups[column_id].columns
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
        config = genotype_data.config
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
        result["genotype_browser"] = config.genotype_browser.enabled
        result["common_report"] = {"enabled": config.common_report.enabled}
        result["enrichment_tool"] = \
            config.enrichment.enabled or result["has_denovo"]
        result["gene_browser"] = config.gene_browser
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
        config = genotype_data.config
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
            key: genotype_data.config.get(key, None) for key in keys
        }
        result["has_denovo"] = genotype_data.has_denovo
        result["has_transmitted"] = genotype_data.has_transmitted
        result["genotype_browser"] = config.genotype_browser.enabled
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
            key: config.genotype_browser.get(key, None) for key in [
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
            and config.genotype_browser.get(
                "has_family_structure_filter", None) is None \
            and result["genotype_browser_config"]["has_family_pheno_filters"] \
            is None:
            result["genotype_browser_config"]["has_family_pheno_filters"] = True

        if result["phenotype_data"] is not None \
            and config.genotype_browser.get(
                "has_person_structure_filter", None) is None \
            and result["genotype_browser_config"]["has_person_pheno_filters"] \
            is None:
            result["genotype_browser_config"]["has_person_pheno_filters"] = True

        table_columns = []
        for column in config.genotype_browser.preview_columns:
            logger.info(
                "processing preview column %s for study %s", column, config.id)

            if column in config.genotype_browser.column_groups:
                new_col = dict(config.genotype_browser.column_groups[column])
                new_col["columns"] = StudyWrapperBase.get_columns_as_sources(
                    config, [column],
                )
                table_columns.append(new_col)
            else:
                if config.genotype_browser.columns.genotype and \
                        column in config.genotype_browser.columns.genotype:
                    table_columns.append(
                        dict(config.genotype_browser.columns.genotype[column]),
                    )
                elif config.genotype_browser.columns.phenotype and \
                        column in config.genotype_browser.columns.phenotype:
                    table_columns.append(
                        dict(config.genotype_browser.columns.phenotype[column]),
                    )
                else:
                    raise KeyError(f"No such column {column} configured!")
        result["genotype_browser_config"]["table_columns"] = table_columns

        result["study_types"] = result["study_type"]
        result["enrichment_tool"] = \
            config.enrichment.enabled or result["has_denovo"]
        result["common_report"] = config.common_report.to_dict()
        del result["common_report"]["file_path"]
        result["person_set_collections"] = person_set_collection_configs
        result["name"] = result["name"] or result["id"]

        result["enrichment"] = config.enrichment.to_dict()
        if "background" in result["enrichment"]:
            if "coding_len_background_model" in \
                    result["enrichment"]["background"]:
                del result["enrichment"]["background"][
                    "coding_len_background_model"]["file"]
            if "samocha_background_model" in \
                    result["enrichment"]["background"]:
                del result["enrichment"]["background"][
                    "samocha_background_model"]["file"]

        result["study_names"] = None
        if result["studies"] is not None:
            logger.debug("found studies in %s", config.id)
            study_names = []
            for study_id in result["studies"]:
                wrapper = gpf_instance.get_wdae_wrapper(study_id)
                if wrapper is None:
                    logger.warning(
                        "no wrapper found for study %s", study_id)
                    continue
                name = (
                    wrapper.config.name
                    if wrapper.config.name is not None
                    else wrapper.config.id
                )
                study_names.append(name)
                result["study_names"] = study_names

        return result

    def query_variants_wdae(
        self, kwargs: dict[str, Any],
        sources: list[dict[str, Any]],
        query_transformer: QueryTransformerProtocol,
        response_transformer: ResponseTransformerProtocol,
        max_variants_count: int | None = 10000,
        *,
        max_variants_message: bool = False,
    ) -> Iterable[list]:
        """Wrap query variants method for WDAE streaming."""
        variants_result = self.query_variants_wdae_streaming(
            kwargs, sources, query_transformer, response_transformer,
            max_variants_count, max_variants_message=max_variants_message)
        return filter(None, variants_result)

    @abstractmethod
    def query_variants_wdae_streaming(
        self, kwargs: dict[str, Any],
        sources: list[dict[str, Any]],
        query_transformer: QueryTransformerProtocol,
        response_transformer: ResponseTransformerProtocol,
        max_variants_count: int | None = 10000,
        *,
        max_variants_message: bool = False,
    ) -> Generator[list | None, None, None]:
        """Wrap query variants method for WDAE streaming."""


class StudyWrapper(StudyWrapperBase):
    """Genotype data study wrapper class for WDAE."""

    # pylint: disable=too-many-instance-attributes
    def __init__(  # type: ignore
        self, genotype_data_study: GenotypeData,
        pheno_data: PhenotypeData | None,
        children: list[StudyWrapper] | None = None,
    ) -> None:

        assert genotype_data_study is not None

        super().__init__(genotype_data_study, pheno_data)

        if children is None:
            self.children = [self]
        else:
            self.children = [*children]

        self.is_remote = False

        self._pheno_values_cache = self._get_all_pheno_values()

        self._init_wdae_config()

    def __getattr__(self, name: str) -> Any:
        return getattr(self.genotype_data, name)

    def _get_all_pheno_values(self) -> dict | None:
        if not self.has_pheno_data \
           or not self.config_columns.phenotype:
            return None

        pheno_values = {}

        for column in self.config_columns.phenotype.values():
            assert column.role
            result = {}
            column_values_iter = self.phenotype_data.get_people_measure_values(
                [column.source], roles=[Role.from_name(column.role)])
            for column_value in column_values_iter:
                result[column_value["family_id"]] = column_value[column.source]

            pheno_column_name = f"{column.source}.{column.role}"
            pheno_values[pheno_column_name] = result
        return pheno_values

    @property
    def is_group(self) -> bool:
        return self.genotype_data.is_group

    @property
    def person_set_collections(self) -> dict[str, PersonSetCollection]:
        return self.genotype_data.person_set_collections

    def get_studies_ids(self, *, leaves: bool = True) -> list[str]:
        return self.genotype_data.get_studies_ids(leaves=leaves)

    def _init_wdae_config(self) -> None:
        genotype_browser_config = self.config.genotype_browser
        if not genotype_browser_config:
            return

        # PERSON AND FAMILY FILTERS
        self.person_filters = genotype_browser_config.person_filters or None
        self.family_filters = genotype_browser_config.family_filters or None

        # GENE SCORES
        if genotype_browser_config.column_groups and \
                "gene_scores" in genotype_browser_config.column_groups:
            self.gene_score_column_sources = [
                genotype_browser_config.columns.genotype[slot].source
                for slot in (
                    genotype_browser_config.column_groups.gene_scores.columns
                    or []
                )
            ]
        else:
            self.gene_score_column_sources = []

        # PREVIEW AND DOWNLOAD COLUMNS
        self.columns = genotype_browser_config.columns
        self.column_groups = genotype_browser_config.column_groups
        self._validate_column_groups()
        self.preview_columns = genotype_browser_config.preview_columns
        if genotype_browser_config.preview_columns_ext:
            self.preview_columns.extend(
                genotype_browser_config.preview_columns_ext)
        self.download_columns = genotype_browser_config.download_columns
        if genotype_browser_config.download_columns_ext:
            self.download_columns.extend(
                genotype_browser_config.download_columns_ext)

        self.summary_preview_columns = \
            genotype_browser_config.summary_preview_columns
        self.summary_download_columns = \
            genotype_browser_config.summary_download_columns

    def _validate_column_groups(self) -> bool:
        genotype_cols = self.columns.get("genotype") or []
        phenotype_cols = self.columns.get("phenotype") or []
        for column_group_name, column_group in self.column_groups.items():
            if column_group is None:
                logger.warning(
                    "bad configuration for column group %s",
                    column_group_name)
                continue
            for column_id in column_group.columns:
                if column_id not in genotype_cols \
                   and column_id not in phenotype_cols:
                    logger.warning(
                        "column %s not defined in configuration", column_id)
                    return False
        return True

    @property
    def config_columns(self) -> Box:
        return cast(Box, self.config.genotype_browser.columns)

    def _collect_runners(
        self, kwargs: dict[str, Any],
        query_transformer: QueryTransformerProtocol,
    ) -> list[QueryRunner]:
        runners = []
        for study_wrapper in self.children:
            try:
                query_kwargs = query_transformer.transform_kwargs(
                    study_wrapper, **kwargs,
                )
            except ValueError:
                logger.exception("Skipping study %s", study_wrapper.study_id)
                continue
            else:
                if query_kwargs is None:
                    logger.info(
                        "study %s skipped", study_wrapper.study_id)
                    continue
            assert study_wrapper.genotype_data is not None

            runners.extend(study_wrapper.genotype_data.create_query_runners(
                regions=query_kwargs.get("regions"),
                genes=query_kwargs.get("genes"),
                effect_types=query_kwargs.get("effect_types"),
                family_ids=query_kwargs.get("family_ids"),
                person_ids=query_kwargs.get("person_ids"),
                person_set_collection=query_kwargs.get(
                    "person_set_collection"),
                inheritance=query_kwargs.get("inheritance"),
                roles=query_kwargs.get("roles"),
                sexes=query_kwargs.get("sexes"),
                affected_statuses=query_kwargs.get("affected_statuses"),
                variant_type=query_kwargs.get("variant_type"),
                real_attr_filter=query_kwargs.get("real_attr_filter"),
                categorical_attr_filter=query_kwargs.get(
                    "categorical_attr_filter"),
                ultra_rare=query_kwargs.get("ultra_rare"),
                frequency_filter=query_kwargs.get("frequency_filter"),
                return_reference=query_kwargs.get("return_reference"),
                return_unknown=query_kwargs.get("return_unknown"),
                limit=query_kwargs.get("limit"),
                study_filters=query_kwargs.get("study_filters"),
                tags_query=query_kwargs.get("tags_query"),
            ))
        return runners

    def query_variants_wdae_streaming(
        self, kwargs: dict[str, Any],
        sources: list[dict[str, Any]],
        query_transformer: QueryTransformerProtocol,
        response_transformer: ResponseTransformerProtocol,
        max_variants_count: int | None = 10000,
        *,
        max_variants_message: bool = False,
    ) -> Generator[list | None, None, None]:
        """Wrap query variants method for WDAE streaming of variants."""
        # pylint: disable=too-many-locals,too-many-branches

        max_variants_count = kwargs.pop("maxVariantsCount", max_variants_count)
        summary_variant_ids = kwargs.pop("summaryVariantIds", None)

        study_filters = None
        if kwargs.get("allowed_studies") is not None:
            study_filters = set(kwargs.pop("allowed_studies"))

        if kwargs.get("studyFilters"):
            if study_filters is not None:
                study_filters = study_filters & set(kwargs.pop("studyFilters"))
            else:
                study_filters = set(kwargs.pop("studyFilters"))

        kwargs["study_filters"] = study_filters

        runners = self._collect_runners(kwargs, query_transformer)

        if summary_variant_ids is None:
            # pylint: disable=unused-argument
            def filter_allele(
                allele: FamilyAllele,  # noqa: ARG001
            ) -> bool:
                return True

        elif len(summary_variant_ids) > 0:
            summary_variant_ids = set(summary_variant_ids)

            def filter_allele(allele: FamilyAllele) -> bool:
                svid = f"{allele.cshl_location}:{allele.cshl_variant}"
                return svid in summary_variant_ids

        else:
            # passed empty list of summary variants; empty result
            return

        start = time.time()
        logger.debug(
            "study wrapper (%s) creating variant transformer...",
            self.name)
        transform = response_transformer.variant_transformer(
            self, self._pheno_values_cache,
        )
        logger.debug(
            "study wrapper (%s) variant transformer created in %.2f sec",
            self.name, time.time() - start)

        index = 0
        seen = set()
        unique_family_variants = kwargs.get("unique_family_variants", False)
        psc_query = query_transformer.extract_person_set_collection_query(
            self, kwargs)

        started = time.time()
        try:
            logger.debug(
                "study wrapper (%s) creating query_result_variants...",
                self.name)
            if len(runners) == 0:
                return
            variants_result = QueryResult(runners, limit=max_variants_count)

            logger.debug(
                "study wrapper (%s) starting query_result_variants...",
                self.name)
            variants_result.start()
            elapsed = time.time() - started
            logger.info(
                "study wrapper (%s) variant result started in %0.3fsec",
                self.name, elapsed)

            with closing(variants_result) as variants:
                for variant in variants:
                    if variant is None:
                        yield None
                        continue
                    v = transform(variant)

                    matched = True
                    for aa in v.matched_alleles:
                        assert not aa.is_reference_allele
                        if not filter_allele(cast(FamilyAllele, aa)):
                            matched = False
                            break
                    if not matched:
                        yield None
                        continue

                    fvuid = variant.fvuid
                    if unique_family_variants and fvuid in seen:
                        continue
                    seen.add(fvuid)

                    index += 1
                    if max_variants_count and index > max_variants_count:
                        if max_variants_message:
                            yield [
                                f"# limit of {max_variants_count} variants "
                                f"reached",
                            ]
                        break
                    row_variant = response_transformer.build_variant_row(
                        self,
                        v, sources,
                        person_set_collection=psc_query.psc_id if psc_query
                        else None)

                    yield row_variant
        except GeneratorExit:
            pass
        finally:
            elapsed = time.time() - started
            logger.info(
                "study wrapper (%s)  query returned %s variants; "
                "closed in %0.3fsec", self.study_id, index, elapsed)

    def _query_gene_view_summary_variants(
        self, query_transformer: QueryTransformerProtocol, **kwargs: Any,
    ) -> Generator[SummaryVariant, None, None]:
        study_filters = None
        if kwargs.get("allowed_studies") is not None:
            study_filters = set(kwargs.pop("allowed_studies"))

        if kwargs.get("studyFilters"):
            if study_filters is not None:
                study_filters = study_filters & set(kwargs.pop("studyFilters"))
            else:
                study_filters = set(kwargs.pop("studyFilters"))

        kwargs["study_filters"] = study_filters

        limit = kwargs.pop("maxVariantsCount", None)
        runners = []
        for study_wrapper in self.children:
            try:
                query_kwargs = query_transformer.transform_kwargs(
                    study_wrapper, **kwargs,
                )
            except ValueError:
                logger.exception("Skipping study %s", study_wrapper.study_id)
                continue
            else:
                if query_kwargs is None:
                    logger.info(
                        "study %s skipped", study_wrapper.study_id)
                    continue
            assert study_wrapper.genotype_data is not None

            runners.extend(
                study_wrapper.genotype_data.create_summary_query_runners(
                    regions=query_kwargs.get("regions"),
                    genes=query_kwargs.get("genes"),
                    effect_types=query_kwargs.get("effect_types"),
                    variant_type=query_kwargs.get("variant_type"),
                    real_attr_filter=query_kwargs.get("real_attr_filter"),
                    category_attr_filter=query_kwargs.get(
                        "category_attr_filter"),
                    ultra_rare=query_kwargs.get("ultra_rare"),
                    frequency_filter=query_kwargs.get("frequency_filter"),
                    return_reference=query_kwargs.get("return_reference"),
                    return_unknown=query_kwargs.get("return_unknown"),
                    limit=query_kwargs.get("limit"),
                    study_filters=query_kwargs.get("study_filters"),
                ),
            )

        try:
            if not runners:
                return

            variants_result = QueryResult(runners, limit=limit)
            started = time.time()
            variants: dict[str, SummaryVariant] = {}
            with closing(variants_result) as result:
                result.start()

                for v in result:
                    print(v)
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
                            "seen_as_denovo": [seen_as_denovo],
                        }
                        v.update_attributes(new_attributes)

                    variants[v.svuid] = v
                    if limit and len(variants) >= limit:
                        break

            elapsed = time.time() - started
            logger.info(
                "processing study %s elapsed: %.3f",
                self.study_id, elapsed)

        finally:
            logger.debug("[DONE] executor closed...")

        yield from variants.values()

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
