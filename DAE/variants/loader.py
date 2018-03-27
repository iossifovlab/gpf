'''
Created on Feb 7, 2018

@author: lubo
'''
from __future__ import print_function
import os

from cyvcf2 import VCF

import numpy as np
import pandas as pd

from numba import jit
from variants.attributes import Role, Sex
from variants.variant import VariantBase


class VCFWrapper(object):

    def __init__(self, filename, region=None):
        self.vcf_file = filename
        self.vcf = VCF(filename, lazy=True)
        self._samples = None
        self._vars = None
        self.region = region

    @property
    def samples(self):
        if self._samples is None:
            self._samples = np.array(self.vcf.samples)
        return self._samples

    @property
    def vars(self):
        if self._vars is None:
            if self.region:
                self._vars = list(self.vcf(self.region))
            else:
                self._vars = list(self.vcf)
        return self._vars


class RawVariantsLoader(object):
    SEP = '!'
    SEP2 = '|'

    def __init__(self, config):
        self.config = config

    def load_annotation(self, storage='csv'):
        assert self.config.annotation
        return self.load_annotation_file(
            self.config.annotation, storage=storage)

    @staticmethod
    def convert_array_of(token, dtype):
        token = token.strip()
        return np.fromstring(token, dtype=dtype, sep=RawVariantsLoader.SEP)

    @staticmethod
    def convert_array_of_ints(token):
        return RawVariantsLoader.convert_array_of(token, int)

    @staticmethod
    def convert_array_of_floats(token):
        return RawVariantsLoader.convert_array_of(token, float)

    @staticmethod
    def convert_array_of_strings(token):
        token = token.strip()
        words = [w.strip() for w in token.split(RawVariantsLoader.SEP)]
        return np.array(words)

    @staticmethod
    def load_annotation_file(filename, sep='\t', storage='csv'):
        assert os.path.exists(filename)
        if storage == 'csv':
            with open(filename, 'r') as infile:
                annot_df = pd.read_csv(
                    infile, sep=sep, index_col=False,
                    dtype={
                        'chr': str,
                        'position': np.int32,
                    },
                    converters={
                        'altA':
                        RawVariantsLoader.convert_array_of_strings,
                        'all.nAltAlls':
                        RawVariantsLoader.convert_array_of_ints,
                        'all.altFreq':
                        RawVariantsLoader.convert_array_of_floats,
                        'effectType':
                        RawVariantsLoader.convert_array_of_strings,
                        'effectGene':
                        RawVariantsLoader.convert_array_of_strings,
                        'effectDetails':
                        RawVariantsLoader.convert_array_of_strings,
                    })
            return annot_df
        elif storage == 'parquet':
            annot_df = pd.read_parquet(filename)
            return annot_df
        else:
            raise ValueError("unexpected input format: {}".format(storage))

    @staticmethod
    def save_annotation_file(vars_df, filename, sep='\t', storage='csv'):
        def convert_array_of_strings(a):
            return RawVariantsLoader.SEP.join(a)

        def convert_array_of_lists(a):
            return RawVariantsLoader.SEP.join(
                [RawVariantsLoader.SEP2.join(str(e)) for e in a]
            )

        def convert_array_of_numbers(a):
            return RawVariantsLoader.SEP.join([
                str(v) for v in a
            ])
        if storage == 'csv':
            vars_df = vars_df.copy()
            vars_df['altA'] = vars_df['altA'].\
                apply(convert_array_of_strings)
            vars_df['effectType'] = vars_df['effectType'].\
                apply(convert_array_of_strings)
            vars_df['effectGene'] = vars_df['effectGene'].\
                apply(convert_array_of_lists)
            vars_df['effectDetails'] = vars_df['effectDetails'].\
                apply(convert_array_of_lists)
            vars_df['all.nAltAlls'] = vars_df['all.nAltAlls'].\
                apply(convert_array_of_numbers)
            vars_df['all.altFreq'] = vars_df['all.altFreq'].\
                apply(convert_array_of_numbers)
            vars_df.to_csv(
                filename,
                index=False,
                sep=sep,
            )
        elif storage == 'parquet':
            vars_df.to_parquet(filename, engine='pyarrow')
        else:
            raise ValueError("unexpected output format: {}".format(storage))

    def load_pedigree(self):
        assert self.config.pedigree
        assert os.path.exists(self.config.pedigree)

        return self.load_pedigree_file(self.config.pedigree)

    @staticmethod
    def load_pedigree_file(infile, sep="\t"):
        ped_df = pd.read_csv(
            infile, sep=sep, index_col=False,
            skipinitialspace=True,
            converters={
                'role': lambda r: Role.from_name(r),
                'sex': lambda s: Sex.from_value(s),
            },
            comment="#",
        )
        if 'sampleId' not in ped_df.columns:
            sample_ids = pd.Series(data=ped_df['personId'].values)
            ped_df['sampleId'] = sample_ids
        return ped_df

    @staticmethod
    def save_pedigree_file(ped_df, filename, storage='csv', sep='\t'):
        assert storage == 'csv'
        ped_df = RawVariantsLoader.sort_pedigree(ped_df.copy())
        ped_df['sex'] = ped_df['sex'].apply(lambda s: s.value)
        if np.all(ped_df['personId'].values == ped_df['sampleId'].values):
            ped_df = ped_df.drop(axis=1, columns=['sampleId'])

        ped_df.to_csv(filename, index=False, sep=sep)

    @staticmethod
    def sort_pedigree(ped_df):
        ped_df['role_order'] = ped_df['role'].apply(lambda r: r.value)
        ped_df = ped_df.sort_values(by=['familyId', 'role_order'])
        ped_df = ped_df.drop(axis=1, columns=['role_order'])
        return ped_df

    def load_vcf(self, region=None):
        assert self.config.vcf
        assert os.path.exists(self.config.vcf)

        return VCFWrapper(self.config.vcf, region)
