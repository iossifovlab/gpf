import logging
import time
from collections.abc import Generator
from contextlib import closing
from typing import Any, cast

import duckdb
import numpy as np
import pandas as pd
import yaml

from dae.genomic_resources.gene_models import GeneModels
from dae.genomic_resources.reference_genome import ReferenceGenome
from dae.inmemory_storage.raw_variants import RawFamilyVariants
from dae.parquet.partition_descriptor import PartitionDescriptor
from dae.parquet.schema2.variant_serializers import VariantsDataSerializer
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
from dae.variants.attributes import Inheritance, Role, Sex, Status
from dae.variants.family_variant import FamilyVariant
from dae.variants.variant import SummaryVariant, SummaryVariantFactory

RealAttrFilterType = list[tuple[str, tuple[float | None, float | None]]]

logger = logging.getLogger(__name__)


class DuckDbRunner(QueryRunner):
    """Run a DuckDb query in a separate thread."""

    def __init__(
            self,
            connection_factory: duckdb.DuckDBPyConnection,
            query: str,
            deserializer: Any | None = None):
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
            logger.exception(
                "exception in runner (%s)",
                self.query)
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
        gene_models: GeneModels | None = None,
        reference_genome: ReferenceGenome | None = None,
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
            self.reference_genome,
        )
        variants_data_schema = self._fetch_variants_data_schema()
        self.serializer = VariantsDataSerializer.build_serializer(
            variants_data_schema,
        )

    def _fetch_meta_property(self, key: str) -> str:
        query = f"""SELECT value FROM {self.layout.meta}
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
        query = f"SELECT * FROM {self.layout.pedigree}"  # noqa: S608
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
        sv_record = self.serializer.deserialize_summary_record(record[3])
        return SummaryVariantFactory.summary_variant_from_records(
            sv_record,
        )

    def _deserialize_family_variant(
        self, record: list[bytes],
    ) -> FamilyVariant:
        sv_record = self.serializer.deserialize_summary_record(record[4])
        fv_record = self.serializer.deserialize_family_record(record[5])
        inheritance_in_members = {
            int(k): [Inheritance.from_value(inh) for inh in v]
            for k, v in fv_record["inheritance_in_members"].items()
        }
        return FamilyVariant(
            SummaryVariantFactory.summary_variant_from_records(
                sv_record,
            ),
            self.families[fv_record["family_id"]],
            np.array(fv_record["genotype"]),
            np.array(fv_record["best_state"]),
            inheritance_in_members=inheritance_in_members,
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
        **kwargs: Any,  # noqa: ARG002
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
        **kwargs: Any,  # noqa: ARG002
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
        **kwargs: Any,  # noqa: ARG002
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
        **kwargs: Any,  # noqa: ARG002
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
