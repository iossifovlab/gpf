import logging
import sys
import time
from collections.abc import Generator
from contextlib import closing
from typing import Any, cast

import duckdb
import pandas as pd
import yaml

from dae.genomic_resources.gene_models import GeneModels
from dae.genomic_resources.reference_genome import ReferenceGenome
from dae.inmemory_storage.raw_variants import RawFamilyVariants
from dae.parquet.partition_descriptor import PartitionDescriptor
from dae.pedigrees.families_data import FamiliesData
from dae.pedigrees.loader import FamiliesLoader
from dae.person_sets import PersonSetCollection
from dae.query_variants.base_query_variants import QueryVariantsBase
from dae.query_variants.query_runners import QueryResult, QueryRunner
from dae.query_variants.sql.schema2.sql_query_builder import (
    Db2Layout,
    SqlQueryBuilder,
)
from dae.utils.regions import Region
from dae.variants.attributes import Role, Sex, Status
from dae.variants.family_variant import FamilyVariant
from dae.variants.variant import SummaryVariant

RealAttrFilterType = list[tuple[str, tuple[float | None, float | None]]]

logger = logging.getLogger(__name__)


class DuckDb2Runner(QueryRunner):
    """Run a DuckDb query in a separate thread."""

    def __init__(
        self,
        connection_factory: duckdb.DuckDBPyConnection,
        query: list[str],
        deserializer: Any | None = None,
        limit: int | None = None,
    ):
        super().__init__(deserializer=deserializer)

        self.connection = connection_factory
        self.query = query
        self.limit = sys.maxsize if limit is None else limit
        self._counter = 0

    def run(self) -> None:
        """Execute the query and enqueue the resulting rows."""
        started = time.time()
        logger.debug(
            "duckdb2 runner (%s) started; running %s queries",
            self.study_id, len(self.query))

        try:
            if self.is_closed():
                logger.info(
                    "runner (%s) closed before execution",
                    self.study_id)
                self._finalize(started)
                return

            for single_query in self.query:
                with self.connection.cursor() as cursor:
                    logger.debug("running SQL query: %s", single_query)
                    cursor.execute(single_query)
                    while record := cursor.fetchone():
                        if record is None:
                            logger.debug("query %s done")
                            break
                        val = self.deserializer(record)
                        if val is None:
                            continue
                        self.put_value_in_result_queue(val)
                        self._counter += 1
                        if self.is_closed():
                            logger.debug(
                                "query runner (%s) closed while iterating",
                                self.study_id)
                            break
                    if self.is_closed() or self._counter >= self.limit:
                        logger.debug(
                            "runner (%s) reached limit: %s",
                            self.study_id, self.limit)
                        break

        except Exception as ex:  # pylint: disable=broad-except
            logger.exception(
                "exception in runner (%s)",
                self.study_id)
            self.put_value_in_result_queue(ex)
        finally:
            logger.debug(
                "runner (%s) closing connection", self.study_id)

        self._finalize(started)

    def _finalize(self, started: float) -> None:
        with self._status_lock:
            self._done = True
        elapsed = time.time() - started
        logger.debug("runner (%s) done in %0.3f sec", self.study_id, elapsed)


class DuckDb2Variants(QueryVariantsBase):
    """Backend for DuckDb storage backend."""

    RUNNER_CLASS = DuckDb2Runner

    def __init__(
        self,
        connection: duckdb.DuckDBPyConnection,
        db2_layout: Db2Layout,
        gene_models: GeneModels,
        reference_genome: ReferenceGenome,
    ) -> None:
        self.connection = connection
        assert self.connection is not None
        self.layout = db2_layout
        logger.debug("working with duckdb2 layout: %s", self.layout)
        self.gene_models = gene_models
        self.reference_genome = reference_genome

        self.start_time = time.time()
        pedigree_schema = self._fetch_pedigree_schema()
        summary_schema = self._fetch_summary_schema()
        family_schema = self._fetch_family_schema()
        schema = SqlQueryBuilder.build_schema(
            pedigree_schema=pedigree_schema,
            summary_schema=summary_schema,
            family_schema=family_schema,
        )
        partition_description = self._fetch_partition_descriptor()
        families = self._fetch_families()
        super().__init__(families)

        self.query_builder = SqlQueryBuilder(
            self.layout,
            schema=schema,
            partition_descriptor=partition_description,
            families=self.families,
            gene_models=self.gene_models,
            reference_genome=self.reference_genome,
        )

    def _fetch_meta_property(self, key: str) -> str:
        meta = self.layout.meta
        if self.layout.db is not None:
            meta = f"{self.layout.db}.{meta}"

        query = f"""SELECT value FROM {meta}
               WHERE key = '{key}'
               LIMIT 1
            """  # noqa: S608
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
        return dict(
            line.split("|") for line in schema_content.split("\n"))

    def _fetch_family_schema(self) -> dict[str, str]:
        schema_content = self._fetch_meta_property("family_schema")
        return dict(
            line.split("|") for line in schema_content.split("\n"))

    def _fetch_pedigree_schema(self) -> dict[str, str]:
        schema_content = self._fetch_meta_property("pedigree_schema")
        if not schema_content:
            return {}
        return dict(
            line.split("|") for line in schema_content.split("\n"))

    def _fetch_variants_data_schema(self) -> dict[str, Any] | None:
        content = self._fetch_meta_property("variants_data_schema")
        if not content:
            return None
        return cast(dict[str, Any], yaml.safe_load(content))

    def _fetch_pedigree(self) -> pd.DataFrame:
        pedigree = self.layout.pedigree
        if self.layout.db is not None:
            pedigree = f"{self.layout.db}.{pedigree}"

        query = f"SELECT * FROM {pedigree}"  # noqa: S608
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

    def _deserialize_summary_variant(
        self, record: list[bytes],
    ) -> SummaryVariant:
        return self.deserialize_summary_variant(
            record[3],
        )

    def _deserialize_family_variant(
        self, record: list[bytes],
    ) -> FamilyVariant:
        return self.deserialize_family_variant(
            record[4], record[5],
        )

    def build_summary_variants_query_runner(
        self, *,
        regions: list[Region] | None = None,
        genes: list[str] | None = None,
        effect_types: list[str] | None = None,
        variant_type: str | None = None,
        real_attr_filter: RealAttrFilterType | None = None,
        ultra_rare: bool | None = None,
        frequency_filter: RealAttrFilterType | None = None,
        return_reference: bool | None = None,
        return_unknown: bool | None = None,
        limit: int | None = None,
        **kwargs: Any,
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
        skip_inmemory_filterng = kwargs.get("skip_inmemory_filterng", False)
        if not skip_inmemory_filterng:
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

    def query_summary_variants(
        self, *,
        regions: list[Region] | None = None,
        genes: list[str] | None = None,
        effect_types: list[str] | None = None,
        variant_type: str | None = None,
        real_attr_filter: RealAttrFilterType | None = None,
        ultra_rare: bool | None = None,
        frequency_filter: RealAttrFilterType | None = None,
        return_reference: bool | None = None,
        return_unknown: bool | None = None,
        limit: int | None = None,
        **kwargs: Any,
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
            **kwargs,
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
        self, *,
        regions: list[Region] | None = None,
        genes: list[str] | None = None,
        effect_types: list[str] | None = None,
        family_ids: list[str] | None = None,
        person_ids: list[str] | None = None,
        inheritance: list[str] | None = None,
        roles: str | None = None,
        sexes: str | None = None,
        variant_type: str | None = None,
        real_attr_filter: RealAttrFilterType | None = None,
        ultra_rare: bool | None = None,
        frequency_filter: RealAttrFilterType | None = None,
        return_reference: bool | None = None,
        return_unknown: bool | None = None,
        limit: int | None = None,
        study_filters: list[str] | None = None,  # noqa: ARG002
        pedigree_fields: tuple | None = None,
        **kwargs: Any,
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
            pedigree_fields=pedigree_fields,
        )
        logger.info("FAMILY VARIANTS QUERY:\n%s", query)

        deserialize_row = self._deserialize_family_variant

        # pylint: disable=protected-access
        runner = self.RUNNER_CLASS(
            connection_factory=self.connection,
            query=query,
            deserializer=deserialize_row)

        skip_inmemory_filterng = kwargs.get("skip_inmemory_filterng", False)
        if not skip_inmemory_filterng:
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

    def query_variants(
        self, *,
        regions: list[Region] | None = None,
        genes: list[str] | None = None,
        effect_types: list[str] | None = None,
        family_ids: list[str] | None = None,
        person_ids: list[str] | None = None,
        inheritance: list[str] | None = None,
        roles: str | None = None,
        sexes: str | None = None,
        variant_type: str | None = None,
        real_attr_filter: RealAttrFilterType | None = None,
        ultra_rare: bool | None = None,
        frequency_filter: RealAttrFilterType | None = None,
        return_reference: bool | None = None,
        return_unknown: bool | None = None,
        limit: int | None = None,
        pedigree_fields: tuple | None = None,
        **kwargs: Any,
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
            pedigree_fields=pedigree_fields,
            **kwargs,
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
            _person_set_collection: PersonSetCollection,
            _person_set_collection_query: tuple[str, set[str]],
    ) -> tuple | tuple[list[str], list[str]] | None:
        """No idea what it does. If you know please edit."""
        return None
