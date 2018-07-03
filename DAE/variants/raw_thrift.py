'''
Created on Jun 26, 2018

@author: lubo
'''
from __future__ import print_function
import os
import numpy as np

from variants.configure import Configure
from variants.family import FamiliesBase, Family
from impala.dbapi import connect
from variants.thrift_query import thrift_query
from variants.parquet_io import read_ped_df_from_parquet
from variants.raw_df import DfFamilyVariantsBase


class ThriftFamilyVariants(FamiliesBase, DfFamilyVariantsBase):

    def __init__(
        self, config=None, prefix=None,
            thrift_host='127.0.0.1', thrift_port=10000,
            thrift_connection=None):

        super(ThriftFamilyVariants, self).__init__()

        if prefix and not config:
            config = Configure.from_prefix_parquet(prefix)

        assert config is not None

        self.config = config.parquet
        assert os.path.exists(self.config.pedigree)
        assert os.path.exists(self.config.summary)
        assert os.path.exists(self.config.family)

        if not thrift_connection:
            thrift_connection = connect(
                host=thrift_host,
                port=thrift_port,
                auth_mechanism='PLAIN')
        self.connection = thrift_connection

        assert self.connection is not None
        self.ped_df = read_ped_df_from_parquet(self.config.pedigree)
        self.families_build(self.ped_df, family_class=Family)

    def query_variants(self, **kwargs):
        df = thrift_query(
            thrift_connection=self.connection,
            summary=self.config.summary,
            family=self.config.family,
            **kwargs
        )
        print(df.genotype, type(df.genotype.values))
        df.genotype = df.genotype.apply(
            lambda v: np.fromstring(v.strip("[]"), dtype=np.int8, sep=','))
        print(df.genotype, type(df.genotype.values))
        print(df[["summary_index", "allele_index",  # "allele_index_fv",
                  "reference",
                  "alternative",  # "alternative_fv",
                  "family_id"]])
        return self.wrap_variants(self.families, df)
