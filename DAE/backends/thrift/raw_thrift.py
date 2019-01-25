'''
Created on Jun 26, 2018

@author: lubo
'''
from __future__ import print_function, unicode_literals, absolute_import
import os
import numpy as np

from impala.dbapi import connect

from variants.family import FamiliesBase, Family
from variants.variant import SummaryVariantFactory
from variants.family_variant import FamilyVariant

from ..configure import Configure
from .thrift_query import thrift_query1
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

        return FamilyVariant(sv, family, gt)

    @staticmethod
    def wrap_variants(families, join_df):
        join_df = join_df.sort_values(
            by=["chrom", "summary_variant_index", "family_id", "allele_index"])
        for _name, group in join_df.groupby(
                by=["chrom", "summary_variant_index", "family_id"]):
            rec = group.to_dict(orient='records')
            yield DfFamilyVariantsBase.wrap_family_variant_multi(families, rec)


class ThriftFamilyVariants(FamiliesBase, DfFamilyVariantsBase):

    def __init__(
        self, config=None, prefix=None,
            thrift_host=None, thrift_port=None,
            thrift_connection=None):

        super(ThriftFamilyVariants, self).__init__()

        if prefix and not config:
            config = Configure.from_prefix_parquet(prefix).parquet

        assert config is not None

        self.config = config
        assert os.path.exists(self.config.pedigree), self.config.pedigree
        assert os.path.exists(self.config.summary_variant), \
            self.config.summary_variant
        assert os.path.exists(self.config.family_variant), \
            self.config.family_variant

        if not thrift_connection:
            thrift_connection = ThriftFamilyVariants.get_thrift_connection(
                thrift_host, thrift_port)
        self.connection = thrift_connection

        assert self.connection is not None
        self.ped_df = read_ped_df_from_parquet(self.config.pedigree)
        self.families_build(self.ped_df, family_class=Family)

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
        # if kwargs.get("effect_types") is not None:
        #     effect_types = kwargs.get("effect_types")
        #     if isinstance(effect_types, list):
        #         effect_types = "any({})".format(",".join(effect_types))
        #         kwargs["effect_types"] = effect_types
        # if kwargs.get("genes") is not None:
        #     genes = kwargs.get("genes")
        #     if isinstance(genes, list):
        #         genes = "any({})".format(",".join(genes))
        #         kwargs["genes"] = genes

        # if kwargs.get("person_ids") is not None:
        #     query = kwargs.get("person_ids")
        #     if isinstance(query, list):
        #         query = "any({})".format(",".join(query))
        #         kwargs["person_ids"] = query

        df = thrift_query1(
            thrift_connection=self.connection,
            tables=self.config,
            query=kwargs
        )

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

        return self.wrap_variants(self.families, df)
