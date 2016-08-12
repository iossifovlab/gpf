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
    DATA_DIRS = [
        "Proband Data",
        # "Designated Unaffected Sibling Data",
        # "Other Sibling Data",
    ]

    def __init__(self):
        self.config = Config()
        self.v14 = self.config._daeConfig.get('sfariDB', 'v14')
        self.v15 = self.config._daeConfig.get('sfariDB', 'v15')
