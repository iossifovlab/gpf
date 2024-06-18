import abc
import logging
from collections.abc import Generator, Iterable
from contextlib import closing
from typing import Any, Optional, Union

import pandas as pd

from dae.genomic_resources.gene_models import GeneModels
from dae.inmemory_storage.raw_variants import RawFamilyVariants
from dae.parquet.partition_descriptor import PartitionDescriptor
from dae.parquet.schema2.variant_serializers import VariantsDataSerializer
from dae.pedigrees.loader import FamiliesLoader
from dae.person_sets import PersonSetCollection
from dae.query_variants.base_query_variants import QueryVariantsBase
from dae.query_variants.query_runners import QueryResult, QueryRunner
from dae.query_variants.sql.schema2.base_query_builder import Dialect
from dae.query_variants.sql.schema2.family_builder import FamilyQueryBuilder
from dae.query_variants.sql.schema2.summary_builder import SummaryQueryBuilder
from dae.utils.regions import Region
from dae.variants.family_variant import FamilyVariant
from dae.variants.variant import SummaryVariant

logger = logging.getLogger(__name__)

RealAttrFilterType = list[tuple[str, tuple[Optional[float], Optional[float]]]]


# pylint: disable=too-many-instance-attributes
class SqlSchema2Variants(QueryVariantsBase):
    """Base class for Schema2 SQL like variants' query interface."""

    RUNNER_CLASS: type[QueryRunner]

    def __init__(
        self,
        dialect: Dialect,
        db: Optional[str],
        family_variant_table: Optional[str],
        summary_allele_table: Optional[str],
        pedigree_table: str,
        meta_table: str,
        gene_models: Optional[GeneModels] = None,
    ):
        assert pedigree_table

        self.dialect = dialect
        self.db = db
        self.family_variant_table = family_variant_table
        self.summary_allele_table = summary_allele_table
        self.has_variants = self.summary_allele_table is not None
        self.pedigree_table = pedigree_table
        self.meta_table = meta_table
        self.gene_models = gene_models

        self.pedigree_schema = self._fetch_schema(self.pedigree_table)
        ped_df = self._fetch_pedigree()
        self.families = FamiliesLoader\
            .build_families_data_from_pedigree(ped_df)

        if self.has_variants:
            self.summary_allele_schema = self._fetch_summary_schema()
            self.family_variant_schema = self._fetch_family_schema()

            self.combined_columns = {
                **self.family_variant_schema,
                **self.summary_allele_schema,
            }

            self.partition_descriptor = PartitionDescriptor.parse_string(
                self._fetch_tblproperties())

        self.serializer = VariantsDataSerializer.build_serializer()

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
    def _fetch_pedigree(self) -> pd.DataFrame:
        """Fetch the pedigree and return it as a data frame."""

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
        regions: Optional[list[Region]] = None,
        genes: Optional[list[str]] = None,
        effect_types: Optional[list[str]] = None,
        variant_type: Optional[str] = None,
        real_attr_filter: Optional[RealAttrFilterType] = None,
        ultra_rare: Optional[bool] = None,
        frequency_filter: Optional[RealAttrFilterType] = None,
        return_reference: Optional[bool] = None,
        return_unknown: Optional[bool] = None,
        limit: Optional[int] = None,
        **kwargs: Any,  # noqa: ARG002
    ) -> QueryRunner:
        """Build a query selecting the appropriate summary variants."""
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

        query = query_builder.build_query(
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
        regions: Optional[list[Region]] = None,
        genes: Optional[list[str]] = None,
        effect_types: Optional[list[str]] = None,
        family_ids: Optional[list[str]] = None,
        person_ids: Optional[list[str]] = None,
        inheritance: Optional[list[str]] = None,
        roles: Optional[str] = None,
        sexes: Optional[str] = None,
        variant_type: Optional[str] = None,
        real_attr_filter: Optional[RealAttrFilterType] = None,
        ultra_rare: Optional[bool] = None,
        frequency_filter: Optional[RealAttrFilterType] = None,
        return_reference: Optional[bool] = None,
        return_unknown: Optional[bool] = None,
        limit: Optional[int] = None,
        study_filters: Optional[list[str]] = None,  # noqa: ARG002
        pedigree_fields: Optional[tuple] = None,
        **kwargs: Any,  # noqa: ARG002
    ) -> QueryRunner:
        """Build a query selecting the appropriate family variants."""
        do_join_pedigree = bool(pedigree_fields)
        do_join_allele_in_members = person_ids is not None

        assert self.family_variant_table is not None
        assert self.summary_allele_table is not None

        query_builder = FamilyQueryBuilder(
            self.dialect,
            self.db,  # type: ignore
            self.family_variant_table,
            self.summary_allele_table,
            self.pedigree_table,
            self.family_variant_schema,
            self.summary_allele_schema,
            self.partition_descriptor.to_dict(),
            self.pedigree_schema,
            self.families,
            gene_models=self.gene_models,
            do_join_pedigree=do_join_pedigree,
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
            variant_type=variant_type,
            real_attr_filter=real_attr_filter,
            ultra_rare=ultra_rare,
            frequency_filter=frequency_filter,
            return_reference=return_reference,
            return_unknown=return_unknown,
            limit=limit,
            pedigree_fields=pedigree_fields,
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
            limit=limit,
            seen=set())

        runner.adapt(filter_func)
        return runner

    def query_summary_variants(
        self, *,
        regions: Optional[list[Region]] = None,
        genes: Optional[list[str]] = None,
        effect_types: Optional[list[str]] = None,
        variant_type: Optional[str] = None,
        real_attr_filter: Optional[RealAttrFilterType] = None,
        ultra_rare: Optional[bool] = None,
        frequency_filter: Optional[RealAttrFilterType] = None,
        return_reference: Optional[bool] = None,
        return_unknown: Optional[bool] = None,
        limit: Optional[int] = None,
        **kwargs: Any,  # noqa: ARG002
    ) -> Generator[SummaryVariant, None, None]:
        """Query summary variants."""
        # pylint: disable=too-many-arguments,too-many-locals
        if limit is None:
            limit = -1
            request_limit = None
        else:
            request_limit = 10 * limit

        runner = self.build_summary_variants_query_runner(
            regions=regions,
            genes=genes,
            effect_types=effect_types,
            variant_type=variant_type,
            real_attr_filter=real_attr_filter,
            ultra_rare=ultra_rare,
            frequency_filter=frequency_filter,
            return_reference=return_reference,
            return_unknown=return_unknown,
            limit=request_limit,
        )

        result = QueryResult(runners=[runner], limit=limit)
        result.start()

        seen = set()
        with closing(result) as result:
            for v in result:
                if v is None:
                    continue
                if v.svuid in seen:
                    continue
                if v is None:
                    continue
                yield v
                seen.add(v.svuid)

    def query_variants(
        self, *,
        regions: Optional[list[Region]] = None,
        genes: Optional[list[str]] = None,
        effect_types: Optional[list[str]] = None,
        family_ids: Optional[list[str]] = None,
        person_ids: Optional[list[str]] = None,
        inheritance: Optional[list[str]] = None,
        roles: Optional[str] = None,
        sexes: Optional[str] = None,
        variant_type: Optional[str] = None,
        real_attr_filter: Optional[RealAttrFilterType] = None,
        ultra_rare: Optional[bool] = None,
        frequency_filter: Optional[RealAttrFilterType] = None,
        return_reference: Optional[bool] = None,
        return_unknown: Optional[bool] = None,
        limit: Optional[int] = None,
        pedigree_fields: Optional[tuple] = None,
        **kwargs: Any,  # noqa: ARG002
    ) -> Generator[FamilyVariant, None, None]:
        """Query family variants."""
        # pylint: disable=too-many-arguments,too-many-locals
        if limit is None:
            limit = -1
            request_limit = None
        else:
            request_limit = 10 * limit

        runner = self.build_family_variants_query_runner(
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
            limit=request_limit,
            pedigree_fields=pedigree_fields,
        )
        result = QueryResult(runners=[runner], limit=limit)

        result.start()
        with closing(result) as result:
            seen = set()
            for v in result:
                if v is None:
                    continue
                if v.fvuid in seen:
                    continue
                yield v
                seen.add(v.fvuid)

    @staticmethod
    def build_person_set_collection_query(
            person_set_collection: PersonSetCollection,
            person_set_collection_query: tuple[str, set[str]],
    ) -> Optional[Union[tuple, tuple[list[str], list[str]]]]:
        """No idea what it does. If you know please edit."""
        collection_id, selected_person_sets = person_set_collection_query
        assert collection_id == person_set_collection.id
        selected_person_sets = set(selected_person_sets)
        assert isinstance(selected_person_sets, set)

        if not person_set_collection.is_pedigree_only():
            return None

        available_person_sets = set(person_set_collection.person_sets.keys())
        if (available_person_sets & selected_person_sets) == \
                available_person_sets:
            return ()

        def pedigree_columns(
            selected_person_sets: Iterable[str],
        ) -> list[dict[str, str]]:
            result = []
            for person_set_id in sorted(selected_person_sets):
                if person_set_id not in person_set_collection.person_sets:
                    continue
                person_set = person_set_collection.person_sets[person_set_id]
                assert len(person_set.values) == \
                    len(person_set_collection.sources)
                person_set_query = {}
                for source, value in zip(
                        person_set_collection.sources, person_set.values):
                    person_set_query[source.ssource] = value
                result.append(person_set_query)
            return result

        if person_set_collection.default.id not in selected_person_sets:
            return (list(pedigree_columns(selected_person_sets)), [])
        return (
            [],
            list(
                pedigree_columns(
                    available_person_sets - selected_person_sets)),
        )
