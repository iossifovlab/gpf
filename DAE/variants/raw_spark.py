'''
Created on Jun 26, 2018

@author: lubo
'''
from __future__ import print_function
import os

from variants.configure import Configure
from variants.family import FamiliesBase
from impala.util import as_pandas
from impala.dbapi import connect


class SparkFamilyVariants(FamiliesBase):

    def __init__(
        self, config=None, prefix=None,
            thrift_host='127.0.0.1', thrift_port=10000,
            thrift_connection=None):
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
