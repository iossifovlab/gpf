import time
import json 
import logging
import sqlparse
from contextlib import closing
from dae.pedigrees.family import FamiliesData
from dae.variants.attributes import Role, Status, Sex
from dae.genome.gene_models import load_gene_models
from dae.utils.variant_utils import mat2str
from dae.backends.schema2.base_query_builder import Dialect
from dae.backends.schema2.family_builder import FamilyQueryBuilder
from dae.backends.schema2.summary_builder import SummaryQueryBuilder
from dae.backends.schema2.base_query_director import QueryDirector
from dae.variants.family_variant import FamilyVariantFactory
from dae.variants.variant import SummaryVariantFactory
from google.cloud import bigquery

logger = logging.getLogger(__name__)

class BigQueryDialect(Dialect):
    def __init__(self, ns: str = None):
        super().__init__(ns=ns)

    def add_unnest_in_join(self) -> bool:
        return True 
    
    def int_type(self) -> str:
        return "INT64"

    def float_type(self) -> str:
        return "FLOAT64"

class BigQueryVariants:

    def __init__(
            self,
            gcp_project_id,
            db,
            summary_allele_table,
            family_variant_table,
            pedigree_table,
            gene_models=None):

        super(BigQueryVariants, self).__init__()
        assert db, db
        assert pedigree_table, pedigree_table

        # instead of a connection handler bigquery has a client object
        self.dialect = BigQueryDialect(ns=gcp_project_id)
        self.client = bigquery.Client(project=gcp_project_id)
        self.db = db
        self.start_time = time.time()

        # family and summary tables
        self.summary_allele_table = summary_allele_table
        self.family_variant_table = family_variant_table
        self.summary_allele_schema= self._fetch_schema(summary_allele_table)
        self.family_variant_schema = self._fetch_schema(family_variant_table)
        self.combined_columns = {**self.family_variant_schema, **self.summary_allele_schema}
        
        # pedigree tables
        self.pedigree_table = pedigree_table
        self.pedigree_schema = self._fetch_schema(self.pedigree_table)
        self.pedigree_df = self._fetch_pedigree()
        self.families = FamiliesData.from_pedigree_df(self.pedigree_df)

        # serializer
        # VariantSchema = namedtuple('VariantSchema', 'col_names')
        # self.variants_schema = VariantSchema(col_names=list(self.combined_columns))
        # self.serializer = AlleleParquetSerializer(variants_schema=self.variants_schema)

        self.gene_models = gene_models
        assert gene_models is not None

        # self._fetch_tblproperties()
        # hardcoding relevant for specific dataset
        # pass in table_properties OR table in datastore
        self.table_properties = dict({
            "region_length": 3000000000,
            "chromosomes": list(map(str, [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13,
                                     14, 15, 16, 17, 18, 19, 20, 21, 22, "X"])),
            "family_bin_size": 2,
            "coding_effect_types": None,
            "rare_boundary": 5
        })

    def _fetch_schema(self, table):
        q = """
            SELECT * FROM {db}.INFORMATION_SCHEMA.COLUMNS
            WHERE table_name = '{table}'
        """.format(
            db=self.db, table=table
        )
        df = self.client.query(q).result().to_dataframe()
        records = df[["column_name", "data_type"]].to_records()
        schema = {
            col_name: col_type for (_, col_name, col_type) in records
        }
        return schema

    def _fetch_pedigree(self):
        q = """
            SELECT * FROM {db}.{pedigree}
        """.format(
            db=self.db, pedigree=self.pedigree_table
        )

        # ped_df = pandas_gbq.read_gbq(q, project_id=self.gcp_project_id)
        ped_df = self.client.query(q).result().to_dataframe()

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

        query = sqlparse.format(query_builder.product, reindent=True, keyword_case='upper')

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

        do_join_affected = affected_status is not None
        query_builder = FamilyQueryBuilder(
                self.dialect, self.db, 
                self.family_variant_table,self.summary_allele_table, self.pedigree_table, 
                self.family_variant_schema, self.summary_allele_schema, self.table_properties, 
                self.pedigree_schema,self.pedigree_df, self.families, 
                gene_models=self.gene_models, 
                do_join_affected=do_join_affected)

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

        query = query_builder.product
        query = sqlparse.format(query_builder.product, reindent=True, keyword_case='upper')

        # ------------------ DEBUG ---------------------
        result = []
        logger.info(f"run kicked at {time.time() - self.start_time}")
        logger.info(f"BQ QUERY BUILDER:\n{query}")
        start = time.perf_counter()
        bq_job = self.client.query(query)
        end = time.perf_counter()
        logger.info(f"TIME (BQ DB): {end - start}")
        result = bq_job
         # ------------------ DEBUG ---------------------

        for row in result:
            try:
                sv_record = json.loads(row.summary_data) 
                fv_record = json.loads(row.family_data)
                fv = FamilyVariantFactory.family_variant_from_record(
                    SummaryVariantFactory.summary_variant_from_records(sv_record),
                    self.families[fv_record["family_id"]],
                    fv_record)
                
                if fv is None:
                    continue
                yield fv
            except Exception as ex:
                logger.error("unable to deserialize family variant (BQ)")
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
            affected_status=None
    ):

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

        logger.debug(f"[DONE] FAMILY VARIANTS QUERY")

if __name__ == "__main__":
    import sys
    from dae import FAMILY_IDS, GENE, CODING_EFFECT_TYPES, GENE_MULTIPLE
    from dae.backends.schema2.impala_variants import ImpalaVariants
    from dae.backends.impala.impala_helpers import ImpalaHelpers
    import pandas as pd

    logging.basicConfig(stream=sys.stdout, level=logging.INFO)

    # count results 
    def count_rows(iter):
        logger.info(f"COUNT: {sum(1 for _ in iter)}")
        iter.close()

    # gather subset of fields to compare BigQuery sets and Impala sets
    def fv_to_df(iter):
        rows = []
        for fv in iter:
            row = {
                'location': fv.location,
                'summary_variant': str(fv.summary_variant),
                'family_id': fv.family_id,
                'best_state': mat2str(fv.gt)
            }
            rows.append(row)
        return pd.DataFrame(rows)

    def df_diff(bq_fv_iter, im_fv_iter):
        bq_df = fv_to_df(bq_fv_iter)
        im_df = fv_to_df(im_fv_iter)

        result = pd.concat([bq_df, im_df]).drop_duplicates(keep=False)

        logger.info(f"BQ row count: {bq_df.shape[0]}")
        logger.info(f"IM row count: {im_df.shape[0]}")

        if (len(result) == 0):
            logger.info(f" {'-'*20} MATCH {'-'*20}")
        else:
            logger.info(f" {'-'*20} MISMATCH {'-'*20}")
            logger.info(result)

        return result
    
    gm = load_gene_models('./reference/refGene-20190211.gz')

    # BigQuery Settings
    project_id = "data-innov"
    db = "sparkv3"
    pedigree_table = 'pedigree'
    family_table = "imported_family_variant"
    summary_table = "imported_summary_allele"
    
    # Impala Settings:
    impala_host = ['localhost']
    impala_port = 21050
    impala_database = 'gpf_variant_db'
    impala_summary_table = 'imported_summary_allele'
    impala_family_table = 'imported_family_variant'
    impala_pedigree_table = 'spakrv3_pilot_pedigree'
    impala_helper = ImpalaHelpers(impala_host, impala_port)

    logger.info("Loading classes and schemas ... ")

    q = BigQueryVariants(project_id, db, 
        summary_table, family_table, pedigree_table, gm)

    i = ImpalaVariants(impala_helper, impala_database, 
        impala_family_table, impala_summary_table, impala_pedigree_table, gm)

    logger.info("Executing queries ... ")
    
    logger.info("101, gene")
    bq = q.query_variants(genes=GENE)
    im = i.query_variants(genes=GENE)
    df_diff(bq, im)

    logger.info("102: gene + effect_type")
    bq = q.query_variants(genes=GENE, effect_types=CODING_EFFECT_TYPES)
    im = i.query_variants(genes=GENE, effect_types=CODING_EFFECT_TYPES)
    df_diff(bq, im)

    logger.info("201: single family_id ")
    bq = q.query_variants(family_ids=FAMILY_IDS[:1])
    im = i.query_variants(family_ids=FAMILY_IDS[:1])
    df_diff(bq, im)

    logger.info("202: single family_id + effect_type")
    bq = q.query_variants(
        family_ids=FAMILY_IDS[:1], effect_types=CODING_EFFECT_TYPES)
    im = i.query_variants(
        family_ids=FAMILY_IDS[:1], effect_types=CODING_EFFECT_TYPES)
    df_diff(bq, im)

    # logger.info("301: single family_id + custom effect_type + af")
    # bq = q.query_variants(
    #     effect_types=['splice-site', 'frame-shift', 'nonsense',
    #                   'no-frame-shift-newStop',
    #                   'noStart', 'noEnd', 'missense', 'no-frame-shift', 'CDS'],
    #     family_ids=FAMILY_IDS[:1],
    #     real_attr_filter=[('af_allele_freq', (None, 1))])
    # im = i.query_variants(
    #     effect_types=['splice-site', 'frame-shift', 'nonsense',
    #                   'no-frame-shift-newStop',
    #                   'noStart', 'noEnd', 'missense', 'no-frame-shift', 'CDS'],
    #     family_ids=FAMILY_IDS[:1],
    #     real_attr_filter=[('af_allele_freq', (None, 1))])
    # df_diff(bq, im)

    # logger.info("401: ultra rare w/ custom effect types")
    # bq = q.query_variants(
    #     effect_types=['splice-site', 'frame-shift', 'nonsense'],
    #     ultra_rare=True)
    # im = i.query_variants(
    #     effect_types=['splice-site', 'frame-shift', 'nonsense'],
    #     ultra_rare=True)
    # df_diff(bq, im)

    # logger.info("501: multiple genes, ultra rare, w/ custom effect types")
    # bq = q.query_variants(
    #     genes=GENE_MULTIPLE,
    #     effect_types=['splice-site', 'frame-shift', 'nonsense'],
    #     ultra_rare=True)

    # im = i.query_variants(
    #     genes=GENE_MULTIPLE,
    #     effect_types=['splice-site', 'frame-shift', 'nonsense'],
    #     ultra_rare=True)
    # df_diff(bq, im)

    # logger.info("601: ultra rare, roles, w/ custom effect type")
    # bq = q.query_variants(
    #     effect_types=['splice-site', 'frame-shift',
    #                   'nonsense', 'no-frame-shift-newStop'],
    #     ultra_rare=True,
    #     roles='prb')
    # im = i.query_variants(
    #     effect_types=['splice-site', 'frame-shift',
    #                   'nonsense', 'no-frame-shift-newStop'],
    #     ultra_rare=True,
    #     roles='prb')
    # df_diff(bq, im)

    # logger.info("701: multiple families, allee_freq, effect type, and role")
    # bq = q.query_variants(
    #     effect_types=['splice-site', 'nonsense', 'missense', 'frame-shift'],
    #     real_attr_filter=[('af_allele_freq', (None, 1))],
    #     family_ids=FAMILY_IDS,
    #     roles='prb')
    # im = i.query_variants(
    #     effect_types=['splice-site', 'nonsense', 'missense', 'frame-shift'],
    #     real_attr_filter=[('af_allele_freq', (None, 1))],
    #     family_ids=FAMILY_IDS,
    #     roles='prb')
    # df_diff(bq, im)

    # logger.info("801: all effects w/ frequency filter")
    # bq = q.query_variants(
    #     effect_types=['splice-site', 'nonsense', 'missense', 'frame-shift'],
    #     real_attr_filter=[('af_allele_freq', (None, 1))],
    #     roles='prb')
    # im = i.query_variants(
    #     effect_types=['splice-site', 'nonsense', 'missense', 'frame-shift'],
    #     real_attr_filter=[('af_allele_freq', (None, 1))],
    #     roles='prb')
    # df_diff(bq, im)

    # 1) build family variant object
    # 2) get the same counts match bigquery + impala investigate table_properties
    # 3) fix combined query
    # 4) prepare for summary / family separation

    # 1) remove pandas dependencies
    # 2) investigate table properties

    # 3) compare deserialized
    # 4) built a set of tuples
    #   (v.location, v.variant, v.familyId,mat2str(v.beststate))
    # set should be the same as count

    # summary variant
    # more long term tasks
    # - Check if new schema works in impala
    # - Direct import into new schema
    # - split the blobs of summary variant and
    # - annotation tables, do we use external tables
    # or do we have append annotations to summary allele table
    # ... not too bad.
    #
    # annotation parallel tables . start preparing
    # hardcoded table properties
    # denovo vs transmitted ultra-rare
    # denovo  => freq bin = 0
    # ultra   => freq bin = 1
    # rare    => freq bin = 2
    # all other => freq bin = 3

    # family bin => how many bins to have? 150
    # ~ hash(family_id) % size = family_bin, pedigree table

    # coding_bin => coding region or outside
    # coding_bin = 0, 1

    # TASKS:
    # - Read code that uses impala variants
    # -- imitated how big query
    # -- look into testing (pytest, integration tests)
    # -- bigquery specific testing (test datasets)
    # - try to move this into GPF
    # - integrating Web UI 

    # from threading import Thread 

    # def query(q):
    #     q.query_variants(genes=GENE)
    #     # count_rows(bq)

    # def cancel(q):
    #     q.cancel_query()

    # def main(t):
    #     # https://docs.python.org/3/library/asyncio-task.html
    #     # Running Tasks Concurrently
    
    #     logger.info("thread: start")
    #     task_query = Thread(target=query, args=[q])
    #     # task_cancel = Thread(target=cancel, args=[q])
    #     task_query.start()
    #     # time.sleep(t)
    #     # task_cancel.start()
    #     task_query.join()
    #     # task_cancel.join()
    #     logger.info("thread:joined")

    # for x in range(100, 101):
    #     main(x)  

    # ImpalaQueryRunner 