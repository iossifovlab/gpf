import time 
import json 
import logging
import numpy as np
from contextlib import closing
from impala.util import as_pandas
from dae.pedigrees.family import FamiliesData
from dae.variants.attributes import Role, Status, Sex
from dae.backends.schema2.base_query_builder import Dialect
from dae.backends.schema2.base_query_director import QueryDirector
from dae.backends.schema2.family_builder import FamilyQueryBuilder
from dae.backends.schema2.summary_builder import SummaryQueryBuilder
from dae.variants.variant import SummaryVariantFactory

logger = logging.getLogger(__name__)


class ImpalaDialect(Dialect):
    def __init__(self):
        super().__init__()


class ImpalaVariants:

    def __init__(
            self,
            impala_helpers,
            db,
            family_variant_table, 
            summary_allele_table, 
            pedigree_table,
            gene_models=None):

        super(ImpalaVariants, self).__init__()
        assert db, db
        assert pedigree_table, pedigree_table

        self.dialect = ImpalaDialect() 
        self.db = db
        self._impala_helpers = impala_helpers
        self.family_variant_table = family_variant_table
        self.summary_allele_table = summary_allele_table
        self.pedigree_table = pedigree_table
        self.summary_allele_schema = self._fetch_schema(self.summary_allele_table)
        self.family_variant_schema = self._fetch_schema(self.family_variant_table)
        self.combined_columns = {**self.family_variant_schema, **self.summary_allele_schema}
        self.pedigree_schema = self._fetch_pedigree_schema()
        self.ped_df = self._fetch_pedigree()
        self.families = FamiliesData.from_pedigree_df(self.ped_df)

        # Serializer 
        # VariantSchema = namedtuple('VariantSchema', 'col_names')
        # self.serializer = AlleleParquetSerializer(
        #     variants_schema=VariantSchema(col_names=list(self.combined_columns))
        # )

        assert gene_models is not None
        self.gene_models = gene_models

        self.table_properties = dict({
            "region_length": 3000000000,
            "chromosomes": list(map(str, [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13,
                                     14, 15, 16, 17, 18, 19, 20, 21, 22, "X"])),
            "family_bin_size": 2,
            "coding_effect_types": None,
            "rare_boundary": 5
        })

        # self._fetch_tblproperties()

    def connection(self):
        conn = self._impala_helpers.connection()
        logger.debug(
            f"getting connection to host {conn.host} from impala helpers "
            f"{id(self._impala_helpers)}")
        return conn

    def _fetch_schema(self, table):
        with closing(self.connection()) as conn:
            with conn.cursor() as cursor:
                q = """
                    DESCRIBE {db}.{table}
                """.format(
                    db=self.db, table=table
                )
                cursor.execute(q)
                df = as_pandas(cursor)

            records = df[["name", "type"]].to_records()
            schema = {
                col_name: col_type for (_, col_name, col_type) in records
            }
            return schema

    def _summary_variants_iterator(
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
        
        query_builder = SummaryQueryBuilder(
                self.dialect, self.db, 
                self.family_variant_table,self.summary_allele_table, self.pedigree_table, 
                self.family_variant_schema, self.summary_allele_schema, self.table_properties, 
                self.pedigree_schema,self.pedigree_df, self.families, 
                gene_models=self.gene_models, 
                do_join_affected=False)

        director = QueryDirector(query_builder)

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

        # query = sqlparse.format(query_builder.product, reindent=True, keyword_case='upper')
        query = query_builder.product
        result = self.client.query(query)

        for row in result:
            try:
                sv_record = json.loads(row.summary_data) 
                sv = SummaryVariantFactory.summary_variant_from_records(sv_record)            
                if sv is None:
                    continue
                yield sv
            except Exception as ex:
                logger.error("unable to deserialize summary variant (BQ)")
                logger.exception(ex)
                continue

    def _family_variants_iterator(
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

        with closing(self.connection()) as conn:

            with conn.cursor() as cursor:
                do_join_affected = affected_status is not None
                query_builder = FamilyQueryBuilder(
                    self.dialect, self.db, self.family_variant_table, self.summary_allele_table, self.pedigree_table,
                    self.family_variant_schema, self.summary_allele_schema, self.table_properties,
                    self.pedigree_schema, self.ped_df,
                    self.families, gene_models=self.gene_models,
                    do_join_affected=do_join_affected
                )
                director = QueryDirector(query_builder)
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
                    affected_status=affected_status
                )

                query = query_builder.product
                # query = sqlparse.format(query_builder.product, reindent=True, keyword_case='upper')
                logger.info(f"FAMILY VARIANTS QUERY ({conn.host}): {query}")

                start = time.perf_counter()
                cursor.execute(query)
                end = time.perf_counter()
                logger.info(f"TIME (IMPALA DB): {end - start}")

                for row in cursor:
                    try:
                        sv_record = json.loads(row.summary_data) 
                        fv_record = json.loads(row.family_data)
                
                        fv = FamilyVariant(
                            SummaryVariantFactory.summary_variant_from_records(sv_record),
                            self.families[fv_record["family_id"]],
                            np.array(fv_record["genotype"]),
                            np.array(fv_record["best_state"]))
                        
                        if fv is None:
                            continue
                        yield fv

                    except Exception as ex:
                        logger.info("unable to deserialize family variant (IMPALA)")
                        logger.exception(ex)
                        continue

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

        if limit is None:
            count = -1
        else:
            count = limit
            limit = 10 * limit

        with closing(self._summary_variants_iterator(
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
                limit=limit)) as sv_iterator:
            
            for sv in sv_iterator:
                if sv is None:
                    continue
                yield sv
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

        if limit is None:
            count = -1
        else:
            count = limit
            limit = 10 * limit

        with closing(self._family_variants_iterator(
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
                        affected_status=affected_status)) as fv_iterator:

            for v in fv_iterator:
                if v is None:
                    continue
                yield v
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
