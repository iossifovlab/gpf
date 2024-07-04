import logging
from collections.abc import Generator, Iterable
from contextlib import closing
from typing import (
    Any,
    Dict,
    List,
    Set,
    Tuple,
    cast,
)

import pandas as pd
import pyarrow as pa
from impala.util import as_pandas
from sqlalchemy import pool

from dae.annotation.annotation_pipeline import AttributeInfo
from dae.genomic_resources.gene_models import GeneModels
from dae.inmemory_storage.raw_variants import RawFamilyVariants
from dae.pedigrees.families_data import FamiliesData
from dae.pedigrees.loader import FamiliesLoader
from dae.person_sets import PersonSetCollection
from dae.query_variants.query_runners import QueryResult
from dae.utils.regions import Region
from dae.variants.attributes import Role, Sex, Status
from dae.variants.family_variant import FamilyVariant
from dae.variants.variant import SummaryVariant
from impala_storage.helpers.impala_helpers import ImpalaHelpers
from impala_storage.helpers.impala_query_runner import ImpalaQueryRunner
from impala_storage.schema1.family_variants_query_builder import (
    FamilyVariantsQueryBuilder,
)
from impala_storage.schema1.schema1_query_director import ImpalaQueryDirector
from impala_storage.schema1.serializers import AlleleParquetSerializer
from impala_storage.schema1.summary_variants_query_builder import (
    SummaryVariantsQueryBuilder,
)

logger = logging.getLogger(__name__)


RealAttrFilterType = list[tuple[str, tuple[float | None, float | None]]]


class ImpalaVariants:
    # pylint: disable=too-many-instance-attributes
    """A backend implementing an impala backend."""

    def __init__(
        self,
        impala_helpers: ImpalaHelpers,
        db: str,
        variants_table: str,
        pedigree_table: str,
        gene_models: GeneModels | None = None,
    ) -> None:
        super().__init__()
        assert db, db
        assert pedigree_table, pedigree_table

        self.db = db
        self.variants_table = variants_table
        self.pedigree_table = pedigree_table

        self._impala_helpers = impala_helpers
        self.pedigree_schema = self._fetch_pedigree_schema()

        ped_df = self._fetch_pedigree()
        self.families = FamiliesData.from_pedigree_df(ped_df)
        # Temporary workaround for studies that are imported without tags
        # e.g. production data that is too large to reimport
        FamiliesLoader._build_families_tags(
            self.families, {"ped_tags": True},
        )

        self.schema = self._fetch_variant_schema()
        if self.variants_table:
            study_id = variants_table.replace("_variants", "").lower()
            self.summary_variants_table = f"{study_id}_summary_variants"
            self.has_summary_variants_table = \
                self._check_summary_variants_table()
            self.serializer = AlleleParquetSerializer(self.schema)

        assert gene_models is not None
        self.gene_models = gene_models

        self.table_properties = dict({
            "region_length": 0,
            "chromosomes": [],
            "family_bin_size": 0,
            "coding_effect_types": [],
            "rare_boundary": 0,
        })
        self._fetch_tblproperties()

    def connection(self) -> pool.PoolProxiedConnection:
        conn = self._impala_helpers.connection()
        return conn

    @property
    def connection_pool(self) -> pool.QueuePool:
        # pylint: disable=protected-access
        return self._impala_helpers._connection_pool

    # @property
    # def executor(self) -> ThreadPoolExecutor:
    #     assert self._impala_helpers.executor is not None
    #     return self._impala_helpers.executor

    # pylint: disable=too-many-arguments,unused-argument
    def build_summary_variants_query_runner(
        self,
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
    ) -> ImpalaQueryRunner | None:
        """Build a query selecting the appropriate summary variants."""
        # pylint: disable=too-many-arguments,too-many-locals
        if not self.variants_table:
            return None
        assert self.schema is not None

        sv_table = None
        if self.has_summary_variants_table:
            sv_table = self.summary_variants_table
        query_builder = SummaryVariantsQueryBuilder(
            self.db, self.variants_table, self.pedigree_table,
            self.schema, self.table_properties,
            self.pedigree_schema, self.families,
            self.gene_models, summary_variants_table=sv_table,
        )
        if limit is None or limit < 0:
            request_limit = None
        else:
            request_limit = limit

        director = ImpalaQueryDirector(query_builder)
        director.build_query(
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

        deserialize_row = query_builder.create_row_deserializer(
            self.serializer,
        )

        query = query_builder.product
        logger.info("SUMMARY VARIANTS QUERY: %s", query)

        runner = ImpalaQueryRunner(
            self.connection_pool, query, deserializer=deserialize_row)

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
            limit=limit)

        runner.adapt(filter_func)

        return runner

    @staticmethod
    def build_person_set_collection_query(
            person_set_collection: PersonSetCollection,
            person_set_collection_query: Tuple[str, Set[str]],
    ) -> tuple | tuple[list[str], list[str]] | None:
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

        def pedigree_columns(selected_person_sets: set) -> list:
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
            pedigree_columns(available_person_sets - selected_person_sets),
        )

    def build_family_variants_query_runner(
        self,
        regions: List[Region] | None = None,
        genes: List[str] | None = None,
        effect_types: List[str] | None = None,
        family_ids: Iterable[str] | None = None,
        person_ids: Iterable[str] | None = None,
        inheritance: List[str] | str | None = None,
        roles: str | None = None,
        sexes: str | None = None,
        variant_type: str | None = None,
        real_attr_filter: RealAttrFilterType | None = None,
        ultra_rare: bool | None = None,
        frequency_filter: RealAttrFilterType | None = None,
        return_reference: bool | None = None,
        return_unknown: bool | None = None,
        limit: int | None = None,
        pedigree_fields: tuple[list[str], list[str]] | None = None,
    ) -> ImpalaQueryRunner | None:
        """Build a query selecting the appropriate family variants."""
        # pylint: disable=too-many-arguments,too-many-locals
        if not self.variants_table:
            logger.debug(
                "missing varants table... skipping")
            return None
        assert self.schema is not None

        do_join = False
        if pedigree_fields is not None:
            do_join = True
        query_builder = FamilyVariantsQueryBuilder(
            self.db, self.variants_table, self.pedigree_table,
            self.schema, self.table_properties,
            self.pedigree_schema,
            self.families, gene_models=self.gene_models,
            do_join=do_join,
        )
        director = ImpalaQueryDirector(query_builder)
        if limit is None or limit < 0:
            request_limit = None
        else:
            request_limit = limit * 10

        director.build_query(
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

        query = query_builder.product

        logger.info("FAMILY VARIANTS QUERY: %s", query)
        deserialize_row = query_builder.create_row_deserializer(
            self.serializer)
        assert deserialize_row is not None

        runner = ImpalaQueryRunner(
            self.connection_pool, query, deserializer=deserialize_row)

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
            limit=limit)

        runner.adapt(filter_func)

        return runner

    # pylint: disable=unused-argument
    def query_summary_variants(
        self,
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
        """Query summary variants."""
        # pylint: disable=too-many-arguments,too-many-locals
        if not self.variants_table:
            return

        if limit is None:
            limit = -1
            request_limit = -1
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
        if runner is None:
            return

        assert runner is not None
        result = QueryResult(runners=[runner], limit=limit)
        logger.debug("starting result")
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
        regions: list[Region] | None = None,
        genes: list[str] | None = None,
        effect_types: list[str] | None = None,
        family_ids: list[str] | None = None,
        person_ids: list[str] | None = None,
        person_set_collection: tuple | None = None,
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
        pedigree_fields: tuple[list[str], list[str]] | None = None,
        **kwargs: Any,
    ) -> Generator[FamilyVariant, None, None]:
        """Query family variants."""
        # pylint: disable=too-many-arguments,too-many-locals
        if not self.variants_table:
            return

        if limit is None:
            limit = -1
            request_limit = -1
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
            pedigree_fields=pedigree_fields)
        if runner is None:
            return

        assert runner is not None
        result = QueryResult(runners=[runner], limit=limit)
        logger.debug("starting result")

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

    def _fetch_pedigree(self) -> pd.DataFrame:
        with closing(self.connection()) as conn:
            with closing(conn.cursor()) as cursor:
                query = f"SELECT * FROM {self.db}.{self.pedigree_table}"""

                cursor.execute(query)
                ped_df = cast(pd.DataFrame, as_pandas(cursor))

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
        if "not_sequenced" in self.pedigree_schema:
            columns = {
                "not_sequenced": "not_sequenced",
            }

        ped_df = ped_df.rename(columns=columns)

        ped_df.role = ped_df.role.apply(Role)  # type: ignore
        ped_df.sex = ped_df.sex.apply(Sex)  # type: ignore
        ped_df.status = ped_df.status.apply(Status)  # type: ignore

        return ped_df

    TYPE_MAP: Dict[str, Any] = {
        "str": ("str", pa.string()),
        "float": ("float", pa.float32()),
        "float32": ("float", pa.float32()),
        "float64": ("float", pa.float64()),
        "int": ("int", pa.int32()),
        "int8": ("int", pa.int8()),
        "tinyint": ("int", pa.int8()),
        "int16": ("int", pa.int16()),
        "smallint": ("int", pa.int16()),
        "int32": ("int", pa.int32()),
        "int64": ("int", pa.int64()),
        "bigint": ("int", pa.int64()),
        "list(str)": ("list", pa.list_(pa.string())),
        "list(float)": ("list", pa.list_(pa.float64())),
        "list(int)": ("list", pa.list_(pa.int32())),
        "bool": ("bool", pa.bool_()),
        "boolean": ("bool", pa.bool_()),
        "binary": ("bytes", pa.binary()),
        "string": ("bytes", pa.string()),
    }

    def _fetch_variant_schema(self) -> list[AttributeInfo] | None:
        if not self.variants_table:
            return None
        with closing(self.connection()) as conn:
            with closing(conn.cursor()) as cursor:
                query = f"DESCRIBE {self.db}.{self.variants_table}"
                cursor.execute(query)
                df = as_pandas(cursor)

            records = df[["name", "type"]].to_records()
            schema_desc = {
                col_name: col_type for (_, col_name, col_type) in records
            }
            schema: list[AttributeInfo] = []
            for name, type_name in schema_desc.items():
                py_type, _ = self.TYPE_MAP[type_name]
                attr = AttributeInfo(name, "table schema", False, {}, py_type)
                schema.append(attr)

            return schema

    def _fetch_pedigree_schema(self) -> Dict[str, str]:
        with closing(self.connection()) as conn:
            with closing(conn.cursor()) as cursor:
                query = f"DESCRIBE {self.db}.{self.pedigree_table}"
                cursor.execute(query)
                df = as_pandas(cursor)
                records = df[["name", "type"]].to_records()
                schema = {
                    col_name: col_type for (_, col_name, col_type) in records
                }
                return schema

    def _fetch_tblproperties(self) -> None:
        if not self.variants_table:
            return
        with closing(self.connection()) as conn:
            with closing(conn.cursor()) as cursor:
                cursor.execute(
                    f"DESCRIBE EXTENDED {self.db}.{self.variants_table}")
                rows = list(cursor)  # type: ignore
                properties_start, properties_end = -1, -1
                for row_index, row in enumerate(rows):
                    if row[0].strip() == "Table Parameters:":
                        properties_start = row_index + 1

                    if (
                        properties_start != -1
                        and row[0] == ""
                        and row[1] is None
                        and row[2] is None
                    ):
                        properties_end = row_index + 1

                if properties_start == -1:
                    logger.debug("No partitioning found")
                    return

                for index in range(properties_start, properties_end):
                    prop_name = rows[index][1]
                    prop_value = rows[index][2]
                    if prop_name == \
                            "gpf_partitioning_region_bin_region_length":
                        self.table_properties["region_length"] = \
                            int(prop_value)
                    elif prop_name == \
                            "gpf_partitioning_region_bin_chromosomes":
                        chromosomes = prop_value.split(",")
                        chromosomes = \
                            list(map(str.strip, chromosomes))
                        self.table_properties["chromosomes"] = chromosomes
                    elif prop_name == \
                            "gpf_partitioning_family_bin_family_bin_size":
                        self.table_properties["family_bin_size"] = \
                            int(prop_value)
                    elif prop_name == \
                            "gpf_partitioning_coding_bin_coding_effect_types":
                        coding_effect_types = prop_value.split(",")
                        coding_effect_types = list(
                            map(str.strip, coding_effect_types))
                        self.table_properties["coding_effect_types"] = \
                            coding_effect_types
                    elif prop_name == \
                            "gpf_partitioning_frequency_bin_rare_boundary":
                        self.table_properties["rare_boundary"] = \
                            float(prop_value)

    def _check_summary_variants_table(self) -> bool:
        with closing(self.connection()) as conn:
            with closing(conn.cursor()) as cursor:
                query = f"SHOW TABLES IN {self.db} " \
                        f"LIKE '{self.summary_variants_table}'"
                cursor.execute(query)
                return len(cursor.fetchall()) == 1
