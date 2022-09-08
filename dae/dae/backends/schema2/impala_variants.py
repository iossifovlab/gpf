import json
import logging
import configparser
from contextlib import closing
from typing import Optional, Set, Tuple
import numpy as np
from impala.util import as_pandas
from dae.person_sets import PersonSetCollection
from dae.backends.query_runners import QueryResult, QueryRunner
from dae.backends.raw.raw_variants import RawFamilyVariants
from dae.backends.schema2.sql_query_runner import SqlQueryRunner
from dae.pedigrees.family import FamiliesData
from dae.pedigrees.loader import FamiliesLoader
from dae.variants.attributes import Role, Status, Sex
from dae.backends.schema2.base_query_builder import Dialect
from dae.backends.schema2.family_builder import FamilyQueryBuilder
from dae.backends.schema2.summary_builder import SummaryQueryBuilder
from dae.variants.variant import SummaryVariantFactory
from dae.variants.family_variant import FamilyVariant

logger = logging.getLogger(__name__)


class ImpalaDialect(Dialect):
    def __init__(self):
        super().__init__()


class ImpalaVariants:
    """A backend implementing an impala backend."""

    # pylint: disable=too-many-instance-attributes

    def __init__(
        self,
        impala_helpers,
        db,
        family_variant_table,
        summary_allele_table,
        pedigree_table,
        meta_table,
        gene_models=None,
    ):

        super().__init__()
        assert db
        assert pedigree_table

        self.dialect = ImpalaDialect()
        self.db = db
        self._impala_helpers = impala_helpers
        self.family_variant_table = family_variant_table
        self.summary_allele_table = summary_allele_table
        self.pedigree_table = pedigree_table
        self.meta_table = meta_table
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
        self.pedigree_schema = self._fetch_pedigree_schema()
        self.ped_df = self._fetch_pedigree()
        self.families = FamiliesData.from_pedigree_df(self.ped_df)
        # Temporary workaround for studies that are imported without tags
        FamiliesLoader._build_families_tags(
            self.families, {"ped_tags": True}
        )

        assert gene_models is not None
        self.gene_models = gene_models

        _tbl_props = self._fetch_tblproperties(self.meta_table)
        self.table_properties = self._normalize_tblproperties(_tbl_props)

    @staticmethod
    def _normalize_tblproperties(tbl_props) -> dict:
        if tbl_props is not None:
            return {
                "region_length": int(
                    tbl_props["region_bin"]["region_length"]
                ),
                "chromosomes": [
                    c.strip()
                    for c in tbl_props["region_bin"]["chromosomes"].split(",")
                ],
                "family_bin_size": int(
                    tbl_props["family_bin"]["family_bin_size"]
                ),
                "rare_boundary": int(
                    tbl_props["frequency_bin"]["rare_boundary"]
                ),
                "coding_effect_types": set(
                    s.strip()
                    for s in tbl_props["coding_bin"][
                        "coding_effect_types"
                    ].split(",")
                ),
            }
        return {
            "region_length": 0,
            "chromosomes": [],
            "family_bin_size": 0,
            "coding_effect_types": set(),
            "rare_boundary": 0
        }

    def connection(self):
        conn = self._impala_helpers.connection()
        logger.debug(
            "getting connection to host %s from impala helpers %s",
            conn.host, id(self._impala_helpers)
        )
        return conn

    def _fetch_schema(self, table) -> dict[str, str]:
        with closing(self.connection()) as conn:
            with conn.cursor() as cursor:
                query = f"""DESCRIBE {self.db}.{table}"""
                cursor.execute(query)
                df = as_pandas(cursor)

            records = df[["name", "type"]].to_records()
            schema = {
                col_name: col_type for (_, col_name, col_type) in records
            }
            return schema

    def _fetch_tblproperties(self, meta_table) \
            -> Optional[configparser.ConfigParser]:
        with closing(self.connection()) as conn:
            with conn.cursor() as cursor:
                query = f"""SELECT value FROM {self.db}.{meta_table}
                            WHERE key = 'partition_description'
                            LIMIT 1
                """

                cursor.execute(query)
                config = configparser.ConfigParser()

                for row in cursor:
                    config.read_string(row[0])
                    return config
        return None

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
            self.table_properties,
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
        runner = SqlQueryRunner(self._impala_helpers._connection_pool, query,
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
            limit=limit)

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
            self.table_properties,
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
        runner = SqlQueryRunner(self._impala_helpers._connection_pool, query,
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
            limit=limit)

        runner.adapt(filter_func)

        return runner

    @staticmethod
    def _deserialize_summary_variant(row):
        sv_record = json.loads(row[-1])
        return SummaryVariantFactory.summary_variant_from_records(sv_record)

    def _deserialize_family_variant(self, row):
        sv_record = json.loads(row[-2])
        fv_record = json.loads(row[-1])

        return FamilyVariant(
            SummaryVariantFactory.summary_variant_from_records(
                sv_record
            ),
            self.families[fv_record["family_id"]],
            np.array(fv_record["genotype"]),
            np.array(fv_record["best_state"]),
        )

    def _fetch_pedigree(self):
        with closing(self.connection()) as conn:
            with conn.cursor() as cursor:
                query = f"""SELECT * FROM {self.db}.{self.pedigree_table}"""
                cursor.execute(query)
                ped_df = as_pandas(cursor)

        ped_df.role = ped_df.role.apply(Role)
        ped_df.sex = ped_df.sex.apply(Sex)
        ped_df.status = ped_df.status.apply(Status)

        return ped_df

    def _fetch_pedigree_schema(self):
        with closing(self.connection()) as conn:
            with conn.cursor() as cursor:
                query = f"""DESCRIBE {self.db}.{self.pedigree_table}"""
                cursor.execute(query)
                df = as_pandas(cursor)

                records = df[["name", "type"]].to_records()
                schema = {
                    col_name: col_type for (_, col_name, col_type) in records
                }
                return schema
