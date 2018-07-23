'''
Created on Jul 23, 2018

@author: lubo
'''
import gzip
import os

import pysam

import pandas as pd
import numpy as np

from variants.configure import Configure
from variants.family import FamiliesBase, Family
import re
from dask.dataframe.io.tests.test_parquet import df


class RawDAE(object):

    SUB_RE = re.compile('^sub\(([ACGT])->([ACGT])\)$')
    INS_RE = re.compile('^ins\(([ACGT]+)\)$')
    DEL_RE = re.compile('^del\((\d+)\)$')

    def __init__(self, summary_filename, toomany_filename, family_filename,
                 region=None, genome=None, annotator=None):
        os.path.exists(summary_filename)
        os.path.exists(toomany_filename)
        os.path.exists(family_filename)

        self.summary_filename = summary_filename
        self.toomany_filename = toomany_filename
        self.region = region
        self.family_filename = family_filename

        self.genome = genome
        self.annotator = annotator

    @staticmethod
    def load_column_names(filename):
        with gzip.open(filename) as infile:
            column_names = infile.readline().strip().split("\t")
        return column_names

    @staticmethod
    def load_region(filename, region):
        column_names = RawDAE.load_column_names(filename)

        with pysam.Tabixfile(filename) as tbf:  # @UndefinedVariable
            infile = tbf.fetch(
                region.chr, region.start, region.stop,
                parser=pysam.asTuple())  # @UndefinedVariable

            df = pd.DataFrame.from_records(
                data=infile, columns=column_names)
        return df

    @staticmethod
    def load(filename):
        with gzip.open(filename) as infile:
            df = pd.read_csv(
                infile,
                dtype={
                    'chr': str,
                },
                sep='\t')
        return df

    def dae2vcf_variant(self, chrom, position, dae_variant):
        match = self.SUB_RE.match(dae_variant)
        if match:
            return chrom, position, match.group(1), match.group(2)

        match = self.INS_RE.match(dae_variant)
        if match:
            alt_suffix = match.group(1)
            reference = self.genome.getSequence(
                chrom, position - 1, position - 1)
            return chrom, position - 1, reference, reference + alt_suffix

        match = self.DEL_RE.match(dae_variant)
        if match:
            count = int(match.group(1))
            reference = self.genome.getSequence(
                chrom, position - 1, position + count - 1)
            return chrom, position - 1, reference, reference[0]

        raise NotImplementedError('weird variant: ' + dae_variant)

    def augment_cshl_variant(self, df):
        result = []
        for _index, row in df.iterrows():
            chrom, position, reference, alternative = self.dae2vcf_variant(
                row['chrom'], row['cshl_position'], row['cshl_variant'])
            result.append({
                "chrom": chrom,
                "position": position,
                "reference": reference,
                "alternative": alternative})
        aug_df = pd.DataFrame.from_records(
            data=result,
            columns=["chrom", "position", "reference", "alternative"])
        assert len(aug_df.index) == len(df.index)

        df['position'] = aug_df['position'].astype(np.int64)
        df['reference'] = aug_df['reference']
        df['alternative'] = aug_df['alternative']

        return df

    def augment_variant_annotation(self, df):
        assert self.annotator is not None

        records = []
        for index, row in df.iterrows():
            records.append(
                (row['chrom'], row['position'],
                 row['reference'], None,
                 index, 0))
            records.append(
                (row['chrom'], row['position'],
                 row['reference'], row['alternative'],
                 index, 1))

        annot_df = pd.DataFrame.from_records(
            data=records,
            columns=[
                'chrom', 'position', 'reference', 'alternative',
                'summary_variant_index',
                'allele_index',
            ])

        # self.annotator.setup(self)
        # annot_df = self.annotator.annotate(df, df)

        return annot_df

    def load_summary_variants(self):
        if self.region:
            df = self.load_region(self.summary_filename, self.region)
        else:
            df = self.load(self.summary_filename)

        df = df.rename(columns={
            "position": "cshl_position",
            "variant": "cshl_variant",
            "chr": "chrom",
        })
        print(df.head())

        df = self.augment_cshl_variant(df)
        df = self.augment_variant_annotation(df)

        return df


class RawDaeVariants(FamiliesBase):

    def __init__(self, config=None, prefix=None, region=None):
        super(RawDaeVariants, self).__init__()

        if prefix is not None:
            config = Configure.from_prefix_dae(prefix)

        assert isinstance(config, Configure)
        assert os.path.exists(config.dae.summary_filename)
        assert os.path.exists(config.dae.toomany_filename)
        assert os.path.exists(config.dae.family_filename)

        self.config = config.dae
        self.region = region

    def _load_families(self):
        self.ped_df = FamiliesBase.load_simple_family_file(
            self.config.family_filename)
        self.families_build(self.ped_df, Family)

    def _load(self, region):
        self._load_families()
