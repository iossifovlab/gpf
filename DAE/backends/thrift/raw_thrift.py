'''
Created on Jun 26, 2018

@author: lubo
'''
from __future__ import print_function, unicode_literals, absolute_import
import os
import numpy as np

from impala.dbapi import connect
from impala.util import as_pandas

from variants.family import FamiliesBase, Family
from variants.variant import SummaryVariantFactory
from variants.family_variant import FamilyVariant

from ..configure import Configure
from .thrift_query import ThriftQueryBuilder
from .parquet_io import read_ped_df_from_parquet


class DfFamilyVariantsBase(object):

    @staticmethod
    def wrap_family_variant_multi(families, records):
        sv = SummaryVariantFactory.summary_variant_from_records(records)

        family_id = records[0]['family_id']
        assert all([r['family_id'] == family_id for r in records])

        family = families[family_id]
        gt = records[0]['genotype']
        gt = gt.reshape([2, len(family)], order='F')
        fv = FamilyVariant(sv, family, gt)
        fv.set_matched_alleles([
            r['allele_index'] for r in records
        ])
        return fv

    @staticmethod
    def wrap_variants(families, join_df):
        join_df = join_df.sort_values(
            by=["bucket_index", "summary_variant_index",
                "family_id", "allele_index"])
        for _name, group in join_df.groupby(
                by=["bucket_index", "summary_variant_index", "family_id"]):
            rec = group.to_dict(orient='records')
            yield DfFamilyVariantsBase.wrap_family_variant_multi(families, rec)


class ThriftFamilyVariants(FamiliesBase, DfFamilyVariantsBase):

    def __init__(
        self, config=None, prefix=None,
            thrift_host=None, thrift_port=None,
            thrift_connection=None, filesystem='local'):

        super(ThriftFamilyVariants, self).__init__()

        if prefix and not config:
            config = Configure.from_prefix_parquet(prefix).parquet

        assert config is not None
        if filesystem == 'local':
            config.summary_variant = "file://" + config.summary_variant
            config.family_variant = "file://" + config.family_variant
            config.member_variant = "file://" + config.member_variant
            config.effect_gene_variant = "file://" + config.effect_gene_variant
            config.pedigree = "file://" + config.pedigree
        self.config = config

        if not thrift_connection:
            thrift_connection = ThriftFamilyVariants.get_thrift_connection(
                thrift_host, thrift_port)
        self.connection = thrift_connection

        assert self.connection is not None
        self.ped_df = read_ped_df_from_parquet(self.config.pedigree)
        self.families_build(self.ped_df, family_class=Family)
        self._summary_schema = None

    @property
    def summary_schema(self):
        if not self._summary_schema:
            query = ThriftQueryBuilder.summary_schema_query(
                tables=self.config)
            with self.connection.cursor() as cursor:
                cursor.execute(query[0])
                cursor.execute(query[1])
                df = as_pandas(cursor)
            records = df[['col_name', 'data_type']].to_records()
            self._summary_schema = {
                col_name: col_type for (_, col_name, col_type) in records
            }
        return self._summary_schema

    @staticmethod
    def get_thrift_connection(thrift_host=None, thrift_port=None):
        if thrift_host is None:
            thrift_host = os.getenv("THRIFTSERVER_HOST", "127.0.0.1")
        if thrift_port is None:
            thrift_port = int(os.getenv("THRIFTSERVER_PORT", 10000))

        thrift_connection = connect(
            host=thrift_host,
            port=thrift_port,
            auth_mechanism='PLAIN')

        return thrift_connection

    def query_variants(self, **kwargs):
        builder = ThriftQueryBuilder(
            kwargs, summary_schema=self.summary_schema,
            tables=self.config, db='parquet')
        sql_query = builder.build()

        if kwargs.get('limit'):
            limit = kwargs['limit']
            sql_query += "\n\tLIMIT {}".format(limit)

        # print("FINAL QUERY", sql_query)
        with self.connection.cursor() as cursor:
            cursor.execute(sql_query)
            df = as_pandas(cursor)

        df.genotype = df.genotype.apply(
            lambda v: np.fromstring(v.strip("[]"), dtype=np.int8, sep=','))

        def s2a(v):
            if v is None:
                return []
            else:
                return v.strip('[]').replace("\"", "")\
                        .replace("'", "").split(",")
        df.effect_gene_types = df.effect_gene_types.apply(s2a)
        df.effect_gene_genes = df.effect_gene_genes.apply(s2a)
        df.effect_details_transcript_ids = \
            df.effect_details_transcript_ids.apply(s2a)
        df.effect_details_details = df.effect_details_details.apply(s2a)

        return self.wrap_variants(self.families, df)
