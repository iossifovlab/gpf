'''
Created on Nov 29, 2016

@author: lubo
'''
from pheno.utils.configuration import PhenoConfig
import os

import pandas as pd


class AgreLoader(PhenoConfig):

    INDIVIDUALS = 'AGRE_Pedigree_Catalog_10-05-2012.csv'

    def __init__(self, *args, **kwargs):
        super(AgreLoader, self).__init__(*args, **kwargs)

    def load_table(self, table_name, roles=['prb'], dtype=None):
        result = []
        for data_dir in self._data_dirs(roles):
            dirname = os.path.join(self['agre', 'dir'], data_dir)
            assert os.path.isdir(dirname)

            filename = os.path.join(dirname, "{}.csv".format(table_name))
            if not os.path.isfile(filename):
                print("skipping {}...".format(filename))
                continue

            print("processing table: {}".format(filename))

            df = pd.read_csv(filename, low_memory=False, dtype=dtype)
            result.append(df)

        return result

    def _load_df(self, name, sep='\t', dtype=None):
        filename = os.path.join(self['agre', 'dir'], name)
        assert os.path.isfile(filename)
        df = pd.read_csv(filename, low_memory=False, sep=sep, dtype=dtype)

        return df

    def load_individuals(self):
        df = self._load_df(self.INDIVIDUALS)
        return df
