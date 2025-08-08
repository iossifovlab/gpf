import abc
import logging
from typing import Any

import pandas as pd

from dae.genomic_resources.gene_models import GeneModels
from dae.inmemory_storage.raw_variants import RawFamilyVariants
from dae.parquet.partition_descriptor import PartitionDescriptor
from dae.pedigrees.loader import FamiliesLoader
from dae.query_variants.base_query_variants import QueryVariantsBase
from dae.query_variants.query_runners import QueryRunner
from dae.query_variants.sql.schema2.base_query_builder import Dialect
from dae.query_variants.sql.schema2.family_builder import FamilyQueryBuilder
from dae.query_variants.sql.schema2.sql_query_builder import TagsQuery
from dae.query_variants.sql.schema2.summary_builder import SummaryQueryBuilder
from dae.utils.regions import Region
from dae.variants.family_variant import FamilyVariant
from dae.variants.variant import SummaryVariant

logger = logging.getLogger(__name__)

RealAttrFilterType = list[tuple[str, tuple[float | None, float | None]]]
CategoricalAttrFilterType = list[tuple[str, list[str] | list[int] | None]]


# pylint: disable=too-many-instance-attributes
class SqlSchema2Variants(QueryVariantsBase):
    """Base class for Schema2 SQL like variants' query interface."""

    RUNNER_CLASS: type[QueryRunner]

    def __init__(
        self,
        dialect: Dialect,
        db: str | None, *,
        family_variant_table: str | None,
        summary_allele_table: str | None,
        pedigree_table: str,
        meta_table: str,
        gene_models: GeneModels | None = None,
    ):
        assert pedigree_table

        self.dialect = dialect
        self.db = db
        logger.debug("workging with db: %s", db)
        self.family_variant_table = family_variant_table
        self.summary_allele_table = summary_allele_table
        self.has_variants = self.summary_allele_table is not None
        self.pedigree_table = pedigree_table
        self.meta_table = meta_table
        self.gene_models = gene_models

        self.pedigree_schema = self._fetch_schema(self.pedigree_table)
        ped_df = self._fetch_pedigree()
        families = FamiliesLoader\
            .build_families_data_from_pedigree(ped_df)

        self.combined_columns = {}
        self.summary_allele_schema = {}
        self.family_variant_schema = {}

        if self.has_variants:
            self.summary_allele_schema = self._fetch_summary_schema()
            self.family_variant_schema = self._fetch_family_schema()

            self.combined_columns = {
                **self.family_variant_schema,
                **self.summary_allele_schema,
            }

        super().__init__(
            families,
            summary_schema=self.summary_allele_schema,
            variants_blob_serializer=self._fetch_variants_blob_serializer(),
        )

        self.partition_descriptor = PartitionDescriptor.parse_string(
                self._fetch_tblproperties())

    def _fetch_summary_schema(self) -> dict[str, str]:
        assert self.summary_allele_table is not None
        return self._fetch_schema(self.summary_allele_table)

    def _fetch_family_schema(self) -> dict[str, str]:
        assert self.family_variant_table is not None
        return self._fetch_schema(self.family_variant_table)

    @abc.abstractmethod
    def _fetch_schema(self, table: str) -> dict[str, str]:
        """Fetch schema of a table and return it as a Dict."""

    @abc.abstractmethod
    def _fetch_variants_data_schema(self) -> dict[str, Any] | None:
        """Fetch variants data schema from metadata table."""

    @abc.abstractmethod
    def _fetch_pedigree(self) -> pd.DataFrame:
        """Fetch the pedigree and return it as a data frame."""

    @abc.abstractmethod
    def _fetch_variants_blob_serializer(self) -> str:
        """Fetch the variants blob serializer from metadata table."""

    @abc.abstractmethod
    def _fetch_tblproperties(self) -> str:
        """Fetch partion description from metadata table."""

    @abc.abstractmethod
    def _get_connection_factory(self) -> Any:
        """Return the connection factory for specific SQL engine."""

    @abc.abstractmethod
    def _deserialize_summary_variant(
        self, record: Any,
    ) -> SummaryVariant:
        """Deserialize a summary variant from SQL record."""

    @abc.abstractmethod
    def _deserialize_family_variant(
        self, record: Any,
    ) -> FamilyVariant:
        """Deserialize a family variant from SQL record."""

    # pylint: disable=too-many-arguments
    def build_summary_variants_query_runner(
        self, *,
        regions: list[Region] | None = None,
        genes: list[str] | None = None,
        effect_types: list[str] | None = None,
        variant_type: str | None = None,
        real_attr_filter: RealAttrFilterType | None = None,
        categorical_attr_filter: CategoricalAttrFilterType | None = None,
        ultra_rare: bool | None = None,
        frequency_filter: RealAttrFilterType | None = None,
        return_reference: bool | None = None,
        return_unknown: bool | None = None,
        limit: int | None = None,
        **kwargs: Any,  # noqa: ARG002
    ) -> QueryRunner | None:
        """Build a query selecting the appropriate summary variants."""
        if self.summary_allele_table is None:
            logger.warning(
                "No summary allele table defined in %s", self.db)
            return None
        assert self.summary_allele_table is not None
        query_builder = SummaryQueryBuilder(
            self.dialect,
            self.db,
            self.family_variant_table,
            self.summary_allele_table,
            self.pedigree_table,
            self.family_variant_schema,
            self.summary_allele_schema,
            self.partition_descriptor.to_dict(),
            self.pedigree_schema,
            self.families,
            gene_models=self.gene_models,
        )
        if limit is None or limit < 0:
            query_limit = None
            limit = -1
        else:
            query_limit = 10 * limit

        query = query_builder.build_query(
            regions=regions,
            genes=genes,
            effect_types=effect_types,
            variant_type=variant_type,
            real_attr_filter=real_attr_filter,
            categorical_attr_filter=categorical_attr_filter,
            ultra_rare=ultra_rare,
            frequency_filter=frequency_filter,
            return_reference=return_reference,
            return_unknown=return_unknown,
            limit=query_limit,
        )
        logger.info("SUMMARY VARIANTS QUERY:\n%s", query)

        # pylint: disable=protected-access
        runner = self.RUNNER_CLASS(
            connection_factory=self._get_connection_factory(),
            query=query,
            deserializer=self._deserialize_summary_variant)

        filter_func = RawFamilyVariants.summary_variant_filter_function(
            regions=regions,
            genes=genes,
            effect_types=effect_types,
            variant_type=variant_type,
            real_attr_filter=real_attr_filter,
            ultra_rare=ultra_rare,
            frequency_filter=frequency_filter,
            return_reference=return_reference,
            return_unknown=return_unknown,
            limit=limit,
            seen=set())

        runner.adapt(filter_func)

        return runner

    # pylint: disable=too-many-arguments,too-many-locals
    def build_family_variants_query_runner(
        self, *,
        regions: list[Region] | None = None,
        genes: list[str] | None = None,
        effect_types: list[str] | None = None,
        family_ids: list[str] | None = None,
        person_ids: list[str] | None = None,
        inheritance: list[str] | None = None,
        roles_in_parent: str | None = None,
        roles_in_child: str | None = None,
        roles: str | None = None,
        sexes: str | None = None,
        affected_statuses: str | None = None,
        variant_type: str | None = None,
        real_attr_filter: RealAttrFilterType | None = None,
        categorical_attr_filter: CategoricalAttrFilterType | None = None,
        ultra_rare: bool | None = None,
        frequency_filter: RealAttrFilterType | None = None,
        return_reference: bool | None = None,
        return_unknown: bool | None = None,
        limit: int | None = None,
        study_filters: list[str] | None = None,  # noqa: ARG002
        tags_query: TagsQuery | None = None,
        **kwargs: Any,  # noqa: ARG002
    ) -> QueryRunner | None:
        """Build a query selecting the appropriate family variants."""
        if self.family_variant_table is None \
                or self.summary_allele_table is None:
            logger.warning(
                "No family or summary allele table defined in %s", self.db)
            return None

        roles = self.transform_roles_to_single_role_string(
            roles_in_parent, roles_in_child, roles)

        tag_family_ids = self.tags_to_family_ids(tags_query)
        if tag_family_ids is not None:
            if family_ids is not None:
                family_ids = list(set(family_ids).intersection(tag_family_ids))
            else:
                family_ids = list(tag_family_ids)

        do_join_allele_in_members = person_ids is not None

        assert self.family_variant_table is not None
        assert self.summary_allele_table is not None
        if limit is None or limit < 0:
            query_limit = None
            limit = -1
        else:
            query_limit = 10 * limit

        query_builder = FamilyQueryBuilder(
            self.dialect,
            self.db,  # type: ignore
            self.family_variant_table,
            self.summary_allele_table,
            self.pedigree_table,
            family_variant_schema=self.family_variant_schema,
            summary_allele_schema=self.summary_allele_schema,
            table_properties=self.partition_descriptor.to_dict(),
            pedigree_schema=self.pedigree_schema,
            families=self.families,
            gene_models=self.gene_models,
            do_join_allele_in_members=do_join_allele_in_members,
        )

        query = query_builder.build_query(
            regions=regions,
            genes=genes,
            effect_types=effect_types,
            family_ids=family_ids,
            person_ids=person_ids,
            inheritance=inheritance,
            roles=roles,
            sexes=sexes,
            affected_statuses=affected_statuses,
            variant_type=variant_type,
            real_attr_filter=real_attr_filter,
            categorical_attr_filter=categorical_attr_filter,
            ultra_rare=ultra_rare,
            frequency_filter=frequency_filter,
            return_reference=return_reference,
            return_unknown=return_unknown,
            limit=query_limit,
        )
        logger.info("FAMILY VARIANTS QUERY:\n%s", query)
        deserialize_row = self._deserialize_family_variant

        # pylint: disable=protected-access
        runner = self.RUNNER_CLASS(
            connection_factory=self._get_connection_factory(),
            query=query,
            deserializer=deserialize_row)

        filter_func = RawFamilyVariants.family_variant_filter_function(
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
            frequency_filter=frequency_filter,
            return_reference=return_reference,
            return_unknown=return_unknown,
        )

        runner.adapt(filter_func)
        return runner
