'''
Created on Feb 7, 2018

@author: lubo
'''
from __future__ import print_function
import os

from cyvcf2 import VCF

import numpy as np
import pandas as pd

from variants.attributes import Role, Sex
from variants.parquet_io import save_summary_to_parquet,\
    read_summary_from_parquet


def save_annotation_to_csv(annot_df, filename, sep="\t"):
    def convert_array_of_strings_to_string(a):
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
        sep=sep,
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
        return self.load_annotation_file(
            self.config.annotation, storage=storage)

    @staticmethod
    def convert_array_of(token, dtype):
        token = token.strip()
        return np.fromstring(token, dtype=dtype, sep=RawVariantsLoader.SEP1)

    @staticmethod
    def convert_array_of_ints(token):
        return RawVariantsLoader.convert_array_of(token, int)

    @staticmethod
    def convert_array_of_floats(token):
        return RawVariantsLoader.convert_array_of(token, float)

    @staticmethod
    def convert_array_of_strings(token):
        token = token.strip()
        words = [w.strip() for w in token.split(RawVariantsLoader.SEP1)]
        return np.array(words)

    @classmethod
    def gene_effects_serialize(cls, all_gene_effects):
        return cls.SEP1.join(
            [cls.SEP2.join(
                [cls.SEP3.join(ge) for ge in gene_effects])
             for gene_effects in all_gene_effects])

    @classmethod
    def gene_effects_deserialize(cls, all_gene_effects):
        return np.array([
            [tuple(ge.split(cls.SEP3))
             for ge in gene_effects.split(cls.SEP2)]
            for gene_effects in all_gene_effects.split(cls.SEP1)
        ])

    @classmethod
    def load_annotation_file(cls, filename, sep='\t', storage='csv'):
        assert os.path.exists(filename)
        if storage == 'csv':
            with open(filename, 'r') as infile:
                annot_df = pd.read_csv(
                    infile, sep=sep, index_col=False,
                    dtype={
                        'chrom': str,
                        'position': np.int32,
                    },
                    converters={
                        'effect_gene_genes':
                        cls.convert_array_of_strings,
                        'effect_gene_types':
                        cls.convert_array_of_strings,
                        'effect_details_transcript_ids':
                        cls.convert_array_of_strings,
                        'effect_details_details':
                        cls.convert_array_of_strings,
                    }
                )
                print(annot_df.head())
            return annot_df
        elif storage == 'parquet':
            annot_df = read_summary_from_parquet(filename)
            return annot_df
        else:
            raise ValueError("unexpected input format: {}".format(storage))

    @classmethod
    def save_annotation_file(cls, annot_df, filename, sep='\t', storage='csv'):

        if storage == 'csv':
            save_annotation_to_csv(annot_df, filename, sep)
        elif storage == 'parquet':
            save_summary_to_parquet(annot_df, filename)
            # vars_df.to_parquet(filename, engine='pyarrow')
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
            dtype={
                'familyId': str,
                'personId': str,
                'sampleId': str,
                'momId': str,
                'dadId': str,
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
