import logging
import abc
from contextlib import closing
from typing import Any, Tuple, Set

import pandas as pd

from dae.person_sets import PersonSetCollection
from dae.pedigrees.family import FamiliesData
from dae.pedigrees.loader import FamiliesLoader
from dae.query_variants.query_runners import QueryResult, QueryRunner
from dae.inmemory_storage.raw_variants import RawFamilyVariants
from dae.parquet.partition_descriptor import PartitionDescriptor
from dae.query_variants.sql.schema2.family_builder import FamilyQueryBuilder
from dae.query_variants.sql.schema2.summary_builder import SummaryQueryBuilder

logger = logging.getLogger(__name__)


# pylint: disable=too-many-instance-attributes
class SqlSchema2Variants(abc.ABC):
    """Base class for Schema2 SQL like variants' query interface."""

    RUNNER_CLASS: type[QueryRunner]

    def __init__(
            self,
            dialect,
            db,
            family_variant_table,
            summary_allele_table,
            pedigree_table,
            meta_table,
            gene_models=None):
        assert db
        assert pedigree_table

        self.dialect = dialect
        self.db = db
        self.family_variant_table = family_variant_table
        self.summary_allele_table = summary_allele_table
        self.pedigree_table = pedigree_table
        self.meta_table = meta_table
        self.gene_models = gene_models

        self.summary_allele_schema = self._fetch_schema(
            self.summary_allele_table
        )
        self.family_variant_schema = self._fetch_schema(
            self.family_variant_table
        )
        self.combined_columns = {
            **self.family_variant_schema,
            **self.summary_allele_schema,
        }

        self.pedigree_schema = self._fetch_schema(self.pedigree_table)
        self.ped_df = self._fetch_pedigree()
        self.families = FamiliesData.from_pedigree_df(self.ped_df)
        # Temporary workaround for studies that are imported without tags
        FamiliesLoader._build_families_tags(
            self.families, {"ped_tags": True}
        )

        self.partition_descriptor = PartitionDescriptor.parse_string(
            self._fetch_tblproperties())

    @abc.abstractmethod
    def _fetch_schema(self, table) -> dict[str, str]:
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
    def _deserialize_summary_variant(self, record):
        """Deserialize a summary variant from SQL record."""

    @abc.abstractmethod
    def _deserialize_family_variant(self, record):
        """Deserialize a family variant from SQL record."""

    # pylint: disable=too-many-arguments
    def build_summary_variants_query_runner(
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
            frequency_filter=None,
            return_reference=None,
            return_unknown=None,
            limit=None) -> QueryRunner:
        """Build a query selecting the appropriate summary variants."""
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
            self.ped_df,
            gene_models=self.gene_models,
            do_join_affected=False,
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
        )
        logger.debug("SUMMARY VARIANTS QUERY: %s", query)

        # pylint: disable=protected-access
        runner = self.RUNNER_CLASS(
            connection_factory=self._get_connection_factory(),
            query=query,
            deserializer=self._deserialize_summary_variant)

        filter_func = RawFamilyVariants.summary_variant_filter_function(
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

    # pylint: disable=too-many-arguments,too-many-locals
    def build_family_variants_query_runner(
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
            frequency_filter=None,
            return_reference=None,
            return_unknown=None,
            limit=None,
            pedigree_fields=None):
        """Build a query selecting the appropriate family variants."""
        do_join_pedigree = pedigree_fields is not None
        query_builder = FamilyQueryBuilder(
            self.dialect,
            self.db,
            self.family_variant_table,
            self.summary_allele_table,
            self.pedigree_table,
            self.family_variant_schema,
            self.summary_allele_schema,
            self.partition_descriptor.to_dict(),
            self.pedigree_schema,
            self.ped_df,
            gene_models=self.gene_models,
            do_join_pedigree=do_join_pedigree,
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
            pedigree_fields=pedigree_fields
        )

        logger.debug("FAMILY VARIANTS QUERY: %s", query)
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
        frequency_filter=None,
        return_reference=None,
        return_unknown=None,
        limit=None,
    ):
        """Query summary variants."""
        # pylint: disable=too-many-arguments,too-many-locals
        if limit is None:
            limit = -1
            request_limit = None
        else:
            request_limit = 10 * limit  # TODO why?

        runner = self.build_summary_variants_query_runner(
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
        frequency_filter=None,
        return_reference=None,
        return_unknown=None,
        limit=None,
        pedigree_fields=None
    ):
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
            pedigree_fields=pedigree_fields
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
            person_set_collection_query: Tuple[str, Set[str]]):
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

        def pedigree_columns(selected_person_sets):
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
            return (pedigree_columns(selected_person_sets), [])
        return (
            [],
            pedigree_columns(available_person_sets - selected_person_sets)
        )
