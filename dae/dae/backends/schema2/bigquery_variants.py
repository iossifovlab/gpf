import time
import json 
import logging
import numpy as np 
from contextlib import closing
from dae.pedigrees.family import FamiliesData
from dae.variants.attributes import Role, Status, Sex
from dae.utils.variant_utils import mat2str
from dae.backends.schema2.base_query_builder import Dialect
from dae.backends.schema2.family_builder import FamilyQueryBuilder
from dae.backends.schema2.summary_builder import SummaryQueryBuilder
from dae.backends.schema2.base_query_director import QueryDirector
from dae.variants.variant import SummaryVariantFactory
from dae.variants.family_variant import FamilyVariant
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
        self.table_properties = {
            "region_length": 100000,
            "chromosomes": list(map(str, [1])),
            "family_bin_size": 5,
            "rare_boundary": 5,
            "coding_effect_types": set("splice-site,frame-shift,nonsense,no-frame-shift-newStop,noStart,noEnd,missense,no-frame-shift,CDS,synonymous,coding_unknown,regulatory,3'UTR,5'UTR".split(","))
        }

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

        # ------------------ DEBUG ---------------------
        result = []
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
                
                fv = FamilyVariant(
                    SummaryVariantFactory.summary_variant_from_records(sv_record),
                    self.families[fv_record["family_id"]],
                    np.array(fv_record["genotype"]),
                    np.array(fv_record["best_state"]))

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

