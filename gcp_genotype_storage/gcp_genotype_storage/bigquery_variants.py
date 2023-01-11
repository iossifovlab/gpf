import time
import json
import logging
from contextlib import closing
from typing import Optional

import configparser
import numpy as np

from google.cloud import bigquery

from dae.pedigrees.family import FamiliesData
from dae.variants.attributes import Role, Status, Sex
from dae.query_variants.sql.schema2.base_query_builder import Dialect
from dae.query_variants.sql.schema2.family_builder import FamilyQueryBuilder
from dae.query_variants.sql.schema2.summary_builder import SummaryQueryBuilder
from dae.variants.variant import SummaryVariantFactory
from dae.variants.family_variant import FamilyVariant

logger = logging.getLogger(__name__)


class BigQueryDialect(Dialect):
    """Abstracts away details related to bigquery."""

    def __init__(self, ns: Optional[str] = None):
        super().__init__(namespace=ns)

    @staticmethod
    def add_unnest_in_join() -> bool:
        return True

    @staticmethod
    def int_type() -> str:
        return "INT64"

    @staticmethod
    def float_type() -> str:
        return "FLOAT64"


# FIXME too-many-instance-attributes
# pylint: disable=too-many-instance-attributes
class BigQueryVariants:
    """Backend for BigQuery."""

    def __init__(
        self,
        gcp_project_id,
        db,
        summary_allele_table,
        family_variant_table,
        pedigree_table,
        meta_table,
        gene_models=None,
    ):

        super().__init__()
        assert db, db
        assert pedigree_table, pedigree_table

        # instead of a connection handler bigquery has a client object
        self.dialect = BigQueryDialect(ns=gcp_project_id)
        self.client = bigquery.Client(project=gcp_project_id)
        self.db = db
        self.start_time = time.time()

        # meta table: partition settings
        self.meta_table = meta_table

        # family and summary tables
        self.summary_allele_table = summary_allele_table
        self.family_variant_table = family_variant_table
        self.summary_allele_schema = self._fetch_schema(summary_allele_table)
        self.family_variant_schema = self._fetch_schema(family_variant_table)
        self.combined_columns = {
            **self.family_variant_schema,
            **self.summary_allele_schema,
        }

        # pedigree tables
        self.pedigree_table = pedigree_table
        self.pedigree_schema = self._fetch_schema(self.pedigree_table)
        self.pedigree_df = self._fetch_pedigree()
        self.families = FamiliesData.from_pedigree_df(self.pedigree_df)

        # serializer
        # VariantSchema = namedtuple('VariantSchema', 'col_names')
        # self.variants_schema = VariantSchema(
        #     col_names=list(self.combined_columns))
        # self.serializer = AlleleParquetSerializer(
        #     variants_schema=self.variants_schema)

        self.gene_models = gene_models
        assert gene_models is not None

        # # self._fetch_tblproperties()
        # # hardcoding relevant for specific dataset
        # # pass in table_properties OR table in datastore
        # _tbl_props = self._fetch_tblproperties(self.meta_table)
        self.table_properties = dict({
            "region_length": 0,
            "chromosomes": [],
            "family_bin_size": 0,
            "coding_effect_types": [],
            "rare_boundary": 0
        })
        # self.table_properties = {
        #     "region_length": int(_tbl_props["region_bin"]["region_length"]),
        #     "chromosomes": list(
        #         map(
        #             lambda c: c.strip(),
        #             _tbl_props["region_bin"]["chromosomes"].split(","),
        #         )
        #     ),
        #     "family_bin_size": int(
        #         _tbl_props["family_bin"]["family_bin_size"]
        #     ),
        #     "rare_boundary": int(
        #           _tbl_props["frequency_bin"]["rare_boundary"]),
        #     "coding_effect_types": {
        #         s.strip()
        #         for s in _tbl_props["coding_bin"][
        #             "coding_effect_types"
        #         ].split(",")
        #     },
        # }

    def _fetch_tblproperties(self, meta_table):
        query = f"""SELECT value FROM {self.db}.{meta_table}
               WHERE key = 'partition_description'
               LIMIT 1
            """

        result = self.client.query(query).result()
        config = configparser.ConfigParser()
        for row in result:
            config.read_string(row[0])
            return config

    def _fetch_schema(self, table):
        query = f"""
            SELECT * FROM {self.db}.INFORMATION_SCHEMA.COLUMNS
            WHERE table_name = '{table}'
        """
        df = self.client.query(query).result().to_dataframe()

        records = df[["column_name", "data_type"]].to_records()
        schema = {col_name: col_type for (_, col_name, col_type) in records}
        return schema

    def _fetch_pedigree(self):
        query = f"SELECT * FROM {self.db}.{self.pedigree_table}"

        # ped_df = pandas_gbq.read_gbq(q, project_id=self.gcp_project_id)
        ped_df = self.client.query(query).result().to_dataframe()

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
            columns = {"not_sequenced": "not_sequenced"}

        ped_df = ped_df.rename(columns=columns)
        ped_df.role = ped_df.role.apply(Role)
        ped_df.sex = ped_df.sex.apply(Sex)
        ped_df.status = ped_df.status.apply(Status)

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
        pedigree_fields=None,
    ):
        # pylint: disable=too-many-arguments,too-many-locals
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
            self.pedigree_df,
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
            pedigree_fields=pedigree_fields,
        )

        result = self.client.query(query)

        for row in result:
            try:
                sv_record = json.loads(row.summary_variant_data)
                sv = SummaryVariantFactory.summary_variant_from_records(
                    sv_record
                )
                if sv is None:
                    continue
                yield sv
            except Exception as ex:  # pylint: disable=broad-except
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
        pedigree_fields=None,
    ):
        # pylint: disable=too-many-arguments,too-many-locals
        do_join_pedigree = pedigree_fields is not None
        query_builder = FamilyQueryBuilder(
            self.dialect,
            self.db,
            family_variant_table=self.family_variant_table,
            summary_allele_table=self.summary_allele_table,
            pedigree_table=self.pedigree_table,
            family_variant_schema=self.family_variant_schema,
            summary_allele_schema=self.summary_allele_schema,
            table_properties=self.table_properties,
            pedigree_schema=self.pedigree_schema,
            pedigree_df=self.pedigree_df,
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
            pedigree_fields=pedigree_fields,
        )

        # ------------------ DEBUG ---------------------
        result = []
        logger.info("BQ QUERY BUILDER:\n%s}", query)
        start = time.perf_counter()
        bq_job = self.client.query(query)
        end = time.perf_counter()
        logger.info("TIME (BQ DB): %f", end - start)
        result = bq_job
        # ------------------ DEBUG ---------------------

        for row in result:
            try:
                sv_record = json.loads(row.summary_variant_data)
                fv_record = json.loads(row.family_variant_data)

                fv = FamilyVariant(
                    SummaryVariantFactory.summary_variant_from_records(
                        sv_record
                    ),
                    self.families[fv_record["family_id"]],
                    np.array(fv_record["genotype"]),
                    np.array(fv_record["best_state"]),
                )

                if fv is None:
                    continue
                yield fv
            except Exception as ex:  # pylint: disable=broad-except
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
        limit=None,
    ):
        """Query summary variants."""
        # FIXME too-many-arguments
        # pylint: disable=too-many-arguments
        if limit is None:
            count = -1
        else:
            count = limit
            limit = 10 * limit

        with closing(
            self._summary_variants_iterator(
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
        ) as sv_iterator:

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
        pedigree_fields=None,
    ):
        """Query summary variants."""
        # FIXME too-many-arguments
        # pylint: disable=too-many-arguments
        if limit is None:
            count = -1
        else:
            count = limit
            limit = 10 * limit

        with closing(
            self._family_variants_iterator(
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
                pedigree_fields=pedigree_fields,
            )
        ) as fv_iterator:

            for v in fv_iterator:
                if v is None:
                    continue
                yield v
                count -= 1
                if count == 0:
                    break

        logger.debug("[DONE] FAMILY VARIANTS QUERY")
