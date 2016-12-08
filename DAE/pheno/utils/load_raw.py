'''
Created on Aug 10, 2016

@author: lubo
'''
import os

import pandas as pd
from pheno.utils.configuration import PhenoConfig


class V14Loader(PhenoConfig):
    MAIN = "SSC_DataDictionary_20120321_Main.csv"
    CDV = "SSC_DataDictionary_20120321_Core_Descriptive_Variables.csv"
    OCUV = "SSC_DataDictionary_20120321_Other_Commonly_Used_Variables.csv"
    CDV_OLD = "SSC_DataDictionary_20120321_cdv.csv"
    OCUV_OLD = "SSC_DataDictionary_20120321_ocuv.csv"

    EVERYTHING = "EVERYTHING.csv"
    COMMON_CORE = "COMMON_CORE.csv"

    def __init__(self, *args, **kwargs):
        super(V14Loader, self).__init__(*args, **kwargs)

    def load_df(self, name, dtype=None):
        filename = os.path.join(self.config.get('ssc_v14', 'dir'), name)
        assert os.path.isfile(filename)
        df = pd.read_csv(filename, low_memory=False, dtype=dtype)

        return df

    def load_main(self):
        return self.load_df(self.config.get('dictionary', 'main'), dtype=str)

    def load_cdv(self):
        return self.load_df(self.config.get('dictionary', 'cdv'), dtype=str)

    def load_ocuv(self):
        return self.load_df(self.config.get('dictionary', 'ocuv'), dtype=str)


class V15Loader(PhenoConfig):
    DATA_DIRS = {
        'prb': [
            'Proband Data',
        ],
        'sib': [
            'Designated Unaffected Sibling Data',
            'Other Sibling Data',
        ],
        'father': [
            'Father Data',
        ],
        'mother': [
            'Mother Data',
        ],
    }

    INDIVIDUALS = "Individuals_by_Distribution_v15.csv"

    def __init__(self, *args, **kwargs):
        super(V15Loader, self).__init__(*args, **kwargs)

    def _data_dirs(self, roles):
        result = []
        for role in roles:
            result.extend(self.DATA_DIRS[role])
        print(result)
        return result

    def load_table(self, table_name, roles=['prb'], dtype=None):
        result = []
        for data_dir in self._data_dirs(roles):
            dirname = os.path.join(self.config.get('ssc_v15', 'dir'), data_dir)
            assert os.path.isdir(dirname)

            filename = os.path.join(dirname, "{}.csv".format(table_name))
            if not os.path.isfile(filename):
                print("skipping {}...".format(filename))
                continue

            print("processing table: {}".format(filename))

            df = pd.read_csv(filename, low_memory=False, dtype=dtype)
            result.append(df)

        return result

    def _load_df(self, name, dtype=None):
        filename = os.path.join(self.config.get('ssc_v15', 'dir'), name)
        assert os.path.isfile(filename)
        df = pd.read_csv(filename, low_memory=False, sep='\t', dtype=dtype)

        return df

    def load_individuals(self):
        df = self._load_df(self.INDIVIDUALS)
        return df
