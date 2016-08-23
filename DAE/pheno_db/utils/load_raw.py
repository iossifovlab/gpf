'''
Created on Aug 10, 2016

@author: lubo
'''
import os

from Config import Config
import pandas as pd


class V14Loader(object):
    MAIN = "SSC_DataDictionary_20120321_Main.csv"
    CDV = "SSC_DataDictionary_20120321_Core_Descriptive_Variables.csv"
    OCUV = "SSC_DataDictionary_20120321_Other_Commonly_Used_Variables.csv"
    CDV_OLD = "SSC_DataDictionary_20120321_cdv.csv"
    OCUV_OLD = "SSC_DataDictionary_20120321_ocuv.csv"

    EVERYTHING = "EVERYTHING.csv"
    COMMON_CORE = "COMMON_CORE.csv"

    def __init__(self):
        self.config = Config()
        self.v14 = self.config._daeConfig.get('sfariDB', 'v14')
        self.v15 = self.config._daeConfig.get('sfariDB', 'v15')

    def _load_df(self, name):
        filename = os.path.join(self.v14, name)
        assert os.path.isfile(filename)
        df = pd.read_csv(filename, low_memory=False)

        return df

    def load_main(self):
        return self._load_df(self.MAIN)

    def load_cdv(self):
        return self._load_df(self.CDV)

    def load_ocuv(self):
        return self._load_df(self.OCUV)

    def load_everything(self):
        return self._load_df(self.EVERYTHING)


class V15Loader(object):
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

    def __init__(self):
        self.config = Config()
        self.v14 = self.config._daeConfig.get('sfariDB', 'v14')
        self.v15 = self.config._daeConfig.get('sfariDB', 'v15')

    def _data_dirs(self, roles):
        result = []
        for role in roles:
            result.extend(self.DATA_DIRS[role])
        print(result)
        return result

    def load_table(self, table_name, roles=['prb']):
        result = []
        for data_dir in self._data_dirs(roles):
            dirname = os.path.join(self.v15, data_dir)
            assert os.path.isdir(dirname)

            filename = os.path.join(dirname, "{}.csv".format(table_name))
            if not os.path.isfile(filename):
                print("skipping {}...".format(filename))
                continue

            print("processing table: {}".format(filename))

            df = pd.read_csv(filename, low_memory=False)
            result.append(df)

        return result

    def _load_df(self, name):
        filename = os.path.join(self.v15, name)
        assert os.path.isfile(filename)
        df = pd.read_csv(filename, low_memory=False, sep='\t')

        return df

    def load_individuals(self):
        df = self._load_df(self.INDIVIDUALS)
        return df
