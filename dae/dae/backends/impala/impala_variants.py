import logging
# from dae.utils.debug_closing import closing
from contextlib import closing
from queue import Queue

from impala.util import as_pandas

from dae.backends.raw.raw_variants import RawFamilyVariants

from dae.annotation.tools.file_io_parquet import ParquetSchema
from dae.pedigrees.family import FamiliesData
from dae.backends.impala.serializers import AlleleParquetSerializer

from dae.variants.attributes import Role, Status, Sex

from dae.backends.impala.impala_helpers import ImpalaQueryResult
from dae.backends.impala.impala_query_director import ImpalaQueryDirector
from dae.backends.impala.family_variants_query_builder import \
    FamilyVariantsQueryBuilder
from dae.backends.impala.summary_variants_query_builder import \
    SummaryVariantsQueryBuilder


logger = logging.getLogger(__name__)


class ImpalaVariants:

    def __init__(
            self,
            impala_helpers,
            db,
            variants_table,
            pedigree_table,
            gene_models=None):

        super(ImpalaVariants, self).__init__()
        assert db, db
        assert pedigree_table, pedigree_table

        self.db = db
        self.variants_table = variants_table
        self.pedigree_table = pedigree_table

        self._impala_helpers = impala_helpers
        self.pedigree_schema = self._fetch_pedigree_schema()

        self.ped_df = self._fetch_pedigree()
        self.families = FamiliesData.from_pedigree_df(self.ped_df)

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
            "rare_boundary": 0
        })
        self._fetch_tblproperties()

    # def count_variants(self, **kwargs):
    #     if not self.variants_table:
    #         return 0
    #     with closing(self.connection()) as conn:
    #         with conn.cursor() as cursor:
    #             query = self.build_count_query(**kwargs)
    #             cursor.execute(query)
    #             row = next(cursor)
    #             return row[0]

    def connection(self):
        conn = self._impala_helpers.connection()
        logger.debug(
            f"getting connection to host {conn.host} from impala helpers "
            f"{id(self._impala_helpers)}")
        return conn

    def _build_summary_variants_query_runner(
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
            limit=None):
        if not self.variants_table:
            return None

        sv_table = None
        if self.has_summary_variants_table:
            sv_table = self.summary_variants_table
        query_builder = SummaryVariantsQueryBuilder(
            self.db, self.variants_table, self.pedigree_table,
            self.schema, self.table_properties,
            self.pedigree_schema, self.ped_df,
            self.gene_models, summary_variants_table=sv_table
        )
        director = ImpalaQueryDirector(query_builder)
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
            limit=None,
        )

        deserialize_row = query_builder.create_row_deserializer(
            self.serializer
        )

        query = query_builder.product
        logger.debug(f"SUMMARY VARIANTS QUERY: {query}")

        runner = self._impala_helpers._submit(
            query, deserializer=deserialize_row)

        return runner

    def _build_family_variants_query_runner(
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
            affected_status=None):

        if not self.variants_table:
            return None
        do_join = affected_status is not None
        query_builder = FamilyVariantsQueryBuilder(
            self.db, self.variants_table, self.pedigree_table,
            self.schema, self.table_properties,
            self.pedigree_schema, self.ped_df,
            self.families, gene_models=self.gene_models,
            do_join=do_join
        )
        director = ImpalaQueryDirector(query_builder)
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
            limit=limit,
            affected_status=affected_status
        )

        query = query_builder.product

        logger.debug(f"FAMILY VARIANTS QUERY: {query}")
        deserialize_row = query_builder.create_row_deserializer(
            self.serializer)

        runner = self._impala_helpers._submit(
            query, deserializer=deserialize_row)

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
            limit=None):
        if not self.variants_table:
            return None

        if limit is None:
            count = -1
        else:
            count = limit
            limit = 10 * limit

        runner = self._build_summary_variants_query_runner(
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
            limit=count)

        runner.adapt(filter_func)

        result_queueu = Queue(maxsize=1_000)
        result = ImpalaQueryResult(
                result_queueu, runners=[runner], limit=count)
        logger.debug("starting result")
        result.start()

        seen = set()
        with closing(result) as result:

            for v in result:
                if v.svuid in seen:
                    continue
                if v is None:
                    continue
                yield v
                seen.add(v.svuid)

                count -= 1
                if count == 0:
                    break

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
            affected_status=None):

        if not self.variants_table:
            return None

        if limit is None:
            count = -1
        else:
            count = limit
            limit = 10 * limit

        runner = self._build_family_variants_query_runner(
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
            affected_status=affected_status)

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
            limit=count)

        runner.adapt(filter_func)

        result_queueu = Queue(maxsize=1_000)
        result = ImpalaQueryResult(
                result_queueu, runners=[runner], limit=count)
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

                count -= 1
                if count == 0:
                    break

    def _fetch_pedigree(self):
        with closing(self.connection()) as conn:
            with conn.cursor() as cursor:
                q = """
                    SELECT * FROM {db}.{pedigree}
                """.format(
                    db=self.db, pedigree=self.pedigree_table
                )

                cursor.execute(q)
                ped_df = as_pandas(cursor)

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
                "not_sequenced": "not_sequenced"
            }

        ped_df = ped_df.rename(columns=columns)

        ped_df.role = ped_df.role.apply(lambda v: Role(v))
        ped_df.sex = ped_df.sex.apply(lambda v: Sex(v))
        ped_df.status = ped_df.status.apply(lambda v: Status(v))

        return ped_df

    def _fetch_variant_schema(self):
        if not self.variants_table:
            return None
        with closing(self.connection()) as conn:
            with conn.cursor() as cursor:
                q = """
                    DESCRIBE {db}.{variant}
                """.format(
                    db=self.db, variant=self.variants_table
                )

                cursor.execute(q)
                df = as_pandas(cursor)

            records = df[["name", "type"]].to_records()
            schema = {
                col_name: col_type for (_, col_name, col_type) in records
            }
            return ParquetSchema(schema)

    def _fetch_pedigree_schema(self):
        with closing(self.connection()) as conn:
            with conn.cursor() as cursor:
                q = """
                    DESCRIBE {db}.{pedigree}
                """.format(
                    db=self.db, pedigree=self.pedigree_table
                )

                cursor.execute(q)
                df = as_pandas(cursor)
                records = df[["name", "type"]].to_records()
                schema = {
                    col_name: col_type for (_, col_name, col_type) in records
                }
                return schema

    def _fetch_tblproperties(self):
        if not self.variants_table:
            return None
        with closing(self.connection()) as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    f"DESCRIBE EXTENDED {self.db}.{self.variants_table}")
                rows = list(cursor)
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
                            int(prop_value)

    def _check_summary_variants_table(self):
        with closing(self.connection()) as conn:
            with conn.cursor() as cursor:
                q = f"SHOW TABLES IN {self.db} " \
                    f"LIKE '{self.summary_variants_table}'"
                cursor.execute(q)
                return len(cursor.fetchall()) == 1

    def build_count_query(
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
        return_reference=None,
        return_unknown=None,
        limit=None,
    ):

        where_clause = self._build_where(
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
            return_reference=return_reference,
            return_unknown=return_unknown,
        )

        return """
            SELECT
                COUNT(
                    DISTINCT
                        bucket_index,
                        summary_variant_index,
                        family_variant_index
                )
            FROM {db}.{variant}
            {where_clause}
            """.format(
            db=self.db, variant=self.variants_table, where_clause=where_clause
        )
