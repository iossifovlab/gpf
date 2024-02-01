import time
import json
import logging
from contextlib import closing
from typing import Optional, Any, Generator, Iterable, Union

import duckdb
import numpy as np
import pandas as pd

from dae.utils.regions import Region
from dae.genomic_resources.gene_models import GeneModels
from dae.genomic_resources.reference_genome import ReferenceGenome
from dae.pedigrees.loader import FamiliesLoader
from dae.pedigrees.families_data import FamiliesData
from dae.person_sets import PersonSetCollection

from dae.variants.attributes import Role, Status, Sex, Inheritance
from dae.query_variants.base_query_variants import \
    QueryVariantsBase
from dae.variants.variant import SummaryVariantFactory, SummaryVariant
from dae.variants.family_variant import FamilyVariant
from dae.parquet.partition_descriptor import PartitionDescriptor
from dae.query_variants.query_runners import QueryRunner, QueryResult
from dae.inmemory_storage.raw_variants import RawFamilyVariants

from dae.query_variants.sql.schema2.sql_query_builder import Db2Layout, \
    SqlQueryBuilder

RealAttrFilterType = list[tuple[str, tuple[Optional[float], Optional[float]]]]

logger = logging.getLogger(__name__)


class DuckDbRunner(QueryRunner):
    """Run a DuckDb query in a separate thread."""

    def __init__(
            self,
            connection_factory: duckdb.DuckDBPyConnection,
            query: str,
            deserializer: Optional[Any] = None):
        super().__init__(deserializer=deserializer)

        self.connection = connection_factory
        self.query = query

    def run(self) -> None:
        """Execute the query and enqueue the resulting rows."""
        started = time.time()
        logger.debug(
            "duckdb runner (%s) started", self.study_id)

        try:
            if self.is_closed():
                logger.info(
                    "runner (%s) closed before execution",
                    self.study_id)
                self._finalize(started)
                return

            with self.connection.cursor() as cursor:
                for record in cursor.execute(self.query).fetchall():
                    val = self.deserializer(record)
                    if val is None:
                        continue
                    self._put_value_in_result_queue(val)
                    if self.is_closed():
                        logger.debug(
                            "query runner (%s) closed while iterating",
                            self.query)
                        break

        except Exception as ex:  # pylint: disable=broad-except
            logger.error(
                "exception in runner (%s) run: %s",
                self.query, type(ex), exc_info=True)
            self._put_value_in_result_queue(ex)
        finally:
            logger.debug(
                "runner (%s) closing connection", self.query)

        self._finalize(started)

    def _finalize(self, started: float) -> None:
        with self._status_lock:
            self._done = True
        elapsed = time.time() - started
        logger.debug("runner (%s) done in %0.3f sec", self.query, elapsed)


class DuckDb2Variants(QueryVariantsBase):
    """Backend for DuckDb storage backend."""

    RUNNER_CLASS = DuckDbRunner

    def __init__(
        self,
        connection: duckdb.DuckDBPyConnection,
        db2_layout: Db2Layout,
        gene_models: Optional[GeneModels] = None,
        reference_genome: Optional[ReferenceGenome] = None,
    ) -> None:
        self.connection = connection
        assert self.connection is not None
        self.layout = db2_layout
        self.gene_models = gene_models
        self.reference_genome = reference_genome

        self.start_time = time.time()
        pedigree_schema = self._fetch_pedigree_schema()
        summary_schema = self._fetch_summary_schema()
        family_schema = self._fetch_family_schema()
        partition_description = self._fetch_partition_descriptor()
        self.families = self._fetch_families()
        self.query_builder = SqlQueryBuilder(
            self.layout,
            pedigree_schema,
            summary_schema,
            family_schema,
            partition_description,
            self.families,
            self.gene_models,
            self.reference_genome
        )

    def _fetch_meta_property(self, key: str) -> str:
        query = f"""SELECT value FROM {self.layout.meta}
               WHERE key = '{key}'
               LIMIT 1
            """
        with self.connection.cursor() as cursor:
            content = ""
            result = cursor.execute(query).fetchall()
            for row in result:
                content = row[0]
        return content

    def _fetch_partition_descriptor(self) -> PartitionDescriptor:
        content = self._fetch_meta_property("partition_description")
        return PartitionDescriptor.parse_string(content)

    def _fetch_summary_schema(self) -> dict[str, str]:
        schema_content = self._fetch_meta_property("summary_schema")
        summary_schema = dict(
            line.split("|") for line in schema_content.split("\n"))
        return summary_schema

    def _fetch_family_schema(self) -> dict[str, str]:
        schema_content = self._fetch_meta_property("family_schema")
        family_schema = dict(
            line.split("|") for line in schema_content.split("\n"))
        return family_schema

    def _fetch_pedigree_schema(self) -> dict[str, str]:
        # query = f"""DESCRIBE {self.layout.pedigree}"""

        # with self.connection.cursor() as cursor:
        #     schema: dict[str, str] = {}
        #     rows = cursor.execute(query).fetchall()
        #     for row in rows:
        #         schema[row[0]] = row[1]

        # return schema
        return {}

    def _fetch_pedigree(self) -> pd.DataFrame:
        query = f"SELECT * FROM {self.layout.pedigree}"
        with self.connection.cursor() as cursor:

            ped_df = cursor.execute(query).df()
            columns = {
                "personId": "person_id",
                "familyId": "family_id",
                "momId": "mom_id",
                "dadId": "dad_id",
                "sampleId": "sample_id",
                "sex": "sex",
                "status": "status",
                "role": "role",
                "generated": "generated",
                "layout": "layout",
                "phenotype": "phenotype",
            }

            ped_df = ped_df.rename(columns=columns)
            ped_df.role = ped_df.role.apply(Role.from_value)  # type: ignore
            ped_df.sex = ped_df.sex.apply(Sex.from_value)  # type: ignore
            ped_df.status = ped_df.status.apply(
                Status.from_value)  # type: ignore
            ped_df.loc[ped_df.layout.isna(), "layout"] = None

            return ped_df

    def _fetch_families(self) -> FamiliesData:
        ped_df = self._fetch_pedigree()
        return FamiliesLoader.build_families_data_from_pedigree(ped_df)

    def _deserialize_summary_variant(self, record: str) -> SummaryVariant:
        sv_record = json.loads(record[3])
        return SummaryVariantFactory.summary_variant_from_records(
            sv_record
        )

    def _deserialize_family_variant(self, record: list[str]) -> FamilyVariant:
        sv_record = json.loads(record[4])
        fv_record = json.loads(record[5])
        inheritance_in_members = {
            int(k): [Inheritance.from_value(inh) for inh in v]
            for k, v in fv_record["inheritance_in_members"].items()
        }
        return FamilyVariant(
            SummaryVariantFactory.summary_variant_from_records(
                sv_record
            ),
            self.families[fv_record["family_id"]],
            np.array(fv_record["genotype"]),
            np.array(fv_record["best_state"]),
            inheritance_in_members=inheritance_in_members
        )

    def build_summary_variants_query_runner(
        self,
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
        **kwargs: Any
    ) -> QueryRunner:
        """Create query runner for searching summary variants."""
        if limit is None or limit < 0:
            query_limit = None
            limit = -1
        else:
            query_limit = 10 * limit

        query = self.query_builder.build_summary_variants_query(
            regions=regions,
            genes=genes,
            effect_types=effect_types,
            variant_type=variant_type,
            real_attr_filter=real_attr_filter,
            ultra_rare=ultra_rare,
            frequency_filter=frequency_filter,
            return_reference=return_reference,
            return_unknown=return_unknown,
            limit=query_limit,
        )
        logger.info("SUMMARY VARIANTS QUERY:\n%s", query)

        runner = self.RUNNER_CLASS(
            connection_factory=self.connection,
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

        # filter_func = \
        #     RawFamilyVariants.summary_variant_filter_duplicate_function()
        runner.adapt(filter_func)

        return runner

    def query_summary_variants(
        self,
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
        **kwargs: Any
    ) -> Generator[SummaryVariant, None, None]:
        """Execute the summary variants query and yields summary variants."""
        if limit is None or limit < 0:
            query_limit = None
            limit = -1
        else:
            query_limit = 10 * limit

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
            limit=query_limit,
        )

        result = QueryResult(runners=[runner], limit=limit)
        result.start()

        with closing(result) as result:
            for v in result:
                if v is None:
                    continue
                yield v
                limit -= 1
                if limit == 0:
                    break

    def build_family_variants_query_runner(
        self,
        regions: Optional[list[Region]] = None,
        genes: Optional[list[str]] = None,
        effect_types: Optional[list[str]] = None,
        family_ids: Optional[list[str]] = None,
        person_ids: Optional[list[str]] = None,
        person_set_collection: Optional[tuple[str, list[str]]] = None,
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
        study_filters: Optional[list[str]] = None,
        pedigree_fields: Optional[tuple] = None,
        **kwargs: Any
    ) -> QueryRunner:
        # pylint: disable=too-many-arguments
        """Create a query runner for searching family variants."""
        if limit is None or limit < 0:
            query_limit = None
            limit = -1
        else:
            query_limit = 10 * limit

        query = self.query_builder.build_family_variants_query(
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
            limit=query_limit,
            pedigree_fields=pedigree_fields
        )
        logger.info("FAMILY VARIANTS QUERY:\n%s", query)
        deserialize_row = self._deserialize_family_variant

        # pylint: disable=protected-access
        runner = self.RUNNER_CLASS(
            connection_factory=self.connection,
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

        # filter_func = \
        #     RawFamilyVariants.family_variant_filter_duplicate_function()
        runner.adapt(filter_func)
        return runner

    def query_variants(
        self,
        regions: Optional[list[Region]] = None,
        genes: Optional[list[str]] = None,
        effect_types: Optional[list[str]] = None,
        family_ids: Optional[list[str]] = None,
        person_ids: Optional[list[str]] = None,
        person_set_collection: Optional[tuple[str, list[str]]] = None,
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
        **kwargs: Any
    ) -> Generator[FamilyVariant, None, None]:
        # pylint: disable=too-many-arguments
        """Execute the family variants query and yields family variants."""
        if limit is None or limit < 0:
            query_limit = None
            limit = -1
        else:
            query_limit = 10 * limit

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
            limit=query_limit,
            pedigree_fields=pedigree_fields
        )
        result = QueryResult(runners=[runner], limit=limit)

        result.start()
        with closing(result) as result:
            for v in result:
                if v is None:
                    continue
                yield v
                limit -= 1
                if limit == 0:
                    break

    @staticmethod
    def build_person_set_collection_query(
            person_set_collection: PersonSetCollection,
            person_set_collection_query: tuple[str, set[str]]
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
            selected_person_sets: Iterable[str]
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
                    available_person_sets - selected_person_sets))
        )
