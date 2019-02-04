'''
Created on Feb 7, 2018

@author: lubo
'''
from __future__ import print_function, absolute_import, unicode_literals

from builtins import object
# from builtins import str
from builtins import open

import os

from cyvcf2 import VCF

import numpy as np
import pandas as pd

# from variants.parquet_io import save_summary_to_parquet,\
#     read_summary_from_parquet


def save_annotation_to_csv(annot_df, filename, sep="\t"):
    def convert_array_of_strings_to_string(a):
        if not a:
            return None
        return RawVariantsLoader.SEP1.join(a)

    vars_df = annot_df.copy()
    vars_df['effect_gene_genes'] = vars_df['effect_gene_genes'].\
        apply(convert_array_of_strings_to_string)
    vars_df['effect_gene_types'] = vars_df['effect_gene_types'].\
        apply(convert_array_of_strings_to_string)
    vars_df['effect_details_transcript_ids'] = \
        vars_df['effect_details_transcript_ids'].\
        apply(convert_array_of_strings_to_string)
    vars_df['effect_details_details'] = \
        vars_df['effect_details_details'].\
        apply(convert_array_of_strings_to_string)
    vars_df.to_csv(
        filename,
        index=False,
        sep=sep
    )


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
    def seqnames(self):
        return self.vcf.seqnames

    @property
    def vars(self):
        if self._vars is None:
            if self.region:
                self._vars = list(self.vcf(self.region))
            else:
                self._vars = list(self.vcf)
        return self._vars


class RawVariantsLoader(object):
    SEP1 = '!'
    SEP2 = '|'
    SEP3 = ':'

    def __init__(self, config):
        self.config = config

    def load_annotation(self, storage='csv'):
        assert self.config.annotation

        if self.has_annotation_file(self.config.annotation):
            return self.load_annotation_file(
                self.config.annotation, storage=storage)
        else:
            # TODO: add test for this
            from .builder import variants_builder
            variants_builder(self.config.prefix)
            return self.load_annotation_file(
                self.config.annotation, storage=storage)

    @staticmethod
    def convert_array_of_strings(token):
        if not token:
            return None
        token = token.strip()
        words = [w.strip() for w in token.split(RawVariantsLoader.SEP1)]
        return words

    @staticmethod
    def convert_string(token):
        if not token:
            return None
        return token

    @staticmethod
    def has_annotation_file(annotation):
        return os.path.exists(annotation)

    @classmethod
    def load_annotation_file(cls, filename, sep='\t', storage='csv'):
        assert os.path.exists(filename)
        assert storage == 'csv'
        if storage == 'csv':
            with open(filename, 'r') as infile:
                annot_df = pd.read_csv(
                    infile, sep=sep, index_col=False,
                    dtype={
                        'chrom': str,
                        'position': np.int32,
                    },
                    converters={
                        'cshl_variant': cls.convert_string,
                        'effect_gene_genes':
                        cls.convert_array_of_strings,
                        'effect_gene_types':
                        cls.convert_array_of_strings,
                        'effect_details_transcript_ids':
                        cls.convert_array_of_strings,
                        'effect_details_details':
                        cls.convert_array_of_strings,
                    },
                    encoding="utf-8"
                )
            for col in ['alternative', 'effect_type']:
                annot_df[col] = annot_df[col].astype(object). \
                    where(pd.notnull(annot_df[col]), None)
            return annot_df
        # elif storage == 'parquet':
        #     annot_df = read_summary_from_parquet(filename)
        #     return annot_df
        else:
            raise ValueError("unexpected input format: {}".format(storage))

    @classmethod
    def save_annotation_file(cls, annot_df, filename, sep='\t', storage='csv'):
        assert storage == 'csv'
        if storage == 'csv':
            save_annotation_to_csv(annot_df, filename, sep)
        # elif storage == 'parquet':
        #     save_summary_to_parquet(annot_df, filename)
        #     # vars_df.to_parquet(filename, engine='pyarrow')
        else:
            raise ValueError("unexpected output format: {}".format(storage))

    def load_vcf(self, region=None):
        assert self.config.vcf
        assert os.path.exists(self.config.vcf)

        return VCFWrapper(self.config.vcf, region)
