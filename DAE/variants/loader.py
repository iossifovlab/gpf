'''
Created on Feb 7, 2018

@author: lubo
'''
from __future__ import print_function
import gzip
import os

from cyvcf2 import VCF

import numpy as np
import pandas as pd

from numba import jit
from variants.roles import Role
from variants.variant import VariantBase


class VCFWrapper(object):

    def __init__(self, filename):
        self.vcf_file = filename
        self.vcf = VCF(filename)
        self._samples = None

    @property
    def samples(self):
        if self._samples is None:
            self._samples = np.array(self.vcf.samples)
        return self._samples


class RawVariantsLoader(object):

    def __init__(self, config):
        self.config = config

    def load_summary(self):
        print(self.config.summary)
        assert self.config.summary
        assert os.path.exists(self.config.summary)

        with gzip.GzipFile(self.config.summary, 'r') as infile:
            sum_df = pd.read_csv(
                infile, sep='\t', index_col=False,
                dtype={
                    'chr': str,
                    'position': np.int32,
                })
        sum_df.drop('familyData', axis=1, inplace=True)
        return sum_df

    def load_pedigree(self):
        assert self.config.pedigree
        assert os.path.exists(self.config.pedigree)

        return self.load_pedigree_file(self.config.pedigree)

    @staticmethod
    def load_pedigree_file(infile):
        ped_df = pd.read_csv(
            infile, sep='\t', index_col=False,
            converters={
                'role': lambda r: Role.from_name(r).value
            }
        )
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
        v1 = VariantBase.from_dae_variant(
            row['chr'], row['position'], row['variant'])

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
        vars_df = loader.load_summary()
        return match_variants(vars_df, vcf)

    def match(self):
        self.vars_df, self.vcf_vars = self._run()
