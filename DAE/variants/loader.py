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

    def __init__(self, filename):
        self.vcf_file = filename
        self.vcf = VCF(filename)
        self._samples = None
        self._vars = None

    @property
    def samples(self):
        if self._samples is None:
            self._samples = np.array(self.vcf.samples)
        return self._samples

    @property
    def vars(self):
        if self._vars is None:
            self._vars = list(self.vcf)
        return self._vars


class RawVariantsLoader(object):

    def __init__(self, config):
        self.config = config

    def load_annotation(self, storage='csv'):
        assert self.config.annotation
        return self.load_annotation_file(
            self.config.annotation, storage=storage)

    @staticmethod
    def convert_array_of(token, dtype):
        token = token.strip()[1:-1]
        return np.fromstring(token, dtype=dtype, sep=' ')

    @staticmethod
    def convert_array_of_ints(token):
        return RawVariantsLoader.convert_array_of(token, int)

    @staticmethod
    def convert_array_of_floats(token):
        return RawVariantsLoader.convert_array_of(token, float)

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
                        'n_alt_alleles': np.object_,
                    },
                    converters={
                        'n_alt_alleles':
                        RawVariantsLoader.convert_array_of_ints,
                        'alt_allele_freq':
                        RawVariantsLoader.convert_array_of_floats,
                    })
            return annot_df
        elif storage == 'parquet':
            annot_df = pd.read_parquet(filename)
            return annot_df
        else:
            raise ValueError("unexpected input format: {}".format(storage))

    @staticmethod
    def save_annotation_file(vars_df, filename, sep='\t', storage='csv'):
        if storage == 'csv':
            vars_df.to_csv(
                filename,
                index=False,
                sep=sep
            )
        elif storage == 'parquet':
            vars_df.to_parquet(filename)
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

    def load_vcf(self):
        assert self.config.vcf
        assert os.path.exists(self.config.vcf)

        return VCFWrapper(self.config.vcf)


@jit
def match_variants(vars_df, vcf):
    vs_iter = iter(vcf.vcf)
    count = 0
    matched = pd.Series(
        data=np.zeros(len(vars_df), dtype=np.bool),
        index=vars_df.index, dtype=np.bool)

    matched_vcf = []
    for index, row in vars_df.iterrows():
        v1 = VariantBase.from_dict(row)

        variant = next(vs_iter)
        v2 = VariantBase.from_vcf_variant(variant)

        while v1 > v2:
            variant = next(vs_iter)
            v2 = VariantBase.from_vcf_variant(variant)

        if v1 < v2:
            continue

        if v1 != v2:
            continue

        count += 1
        matched[index] = True
        matched_vcf.append(variant)

    print("matched variants: ", count)
    vars_df = vars_df[matched]
    vars_df.reset_index(level=0, drop=True, inplace=True)

    assert len(vars_df) == len(matched_vcf)

    return vars_df, matched_vcf


class VariantMatcher(object):

    def __init__(self, config):
        self.config = config
        self.vars_df = None
        self.vcf_vars = None

    def _run(self):
        loader = RawVariantsLoader(self.config)
        vcf = loader.load_vcf()
        vars_df = loader.load_annotation()
        return match_variants(vars_df, vcf)

    def match(self):
        self.vars_df, self.vcf_vars = self._run()
