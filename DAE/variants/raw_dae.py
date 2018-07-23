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
from pprint import pprint


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

    @staticmethod
    def split_gene_effects(data):
        print(data)
        if data == 'intergenic':
            return ['intergenic'], ['intergenic']

        res = [ge.split(':') for ge in data.split(';')]
        genes = [ge[0] for ge in res]
        effects = [ge[1] for ge in res]
        return genes, effects

    def augment_variant_annotation(self, df):
        assert self.annotator is None

        records = []
        for index, rec in enumerate(df.to_dict(orient='records')):
            parents_called = rec['all.nParCalled']
            ref_allele_count = 2 * rec['all.nParCalled'] - rec['all.nAltAlls']
            ref_allele_prcnt = 0.0
            if parents_called > 0:
                ref_allele_prcnt = ref_allele_count / 2.0 / parents_called
            ref = {
                'chrom': rec['chrom'],
                'position': rec['position'],
                'reference': rec['reference'],
                'alternative': None,
                'summary_variant_index': index,
                'allele_index': 0,
                'effect_type': None,
                'effect_gene_genes': None,
                'effect_gene_types': None,
                'effect_details_transcript_ids': None,
                'effect_details_details': None,
                'af_parents_called_count': parents_called,
                'af_parents_called_percent': rec['all.prcntParCalled'],
                'af_allele_count': ref_allele_count,
                'af_allele_freq': ref_allele_prcnt,
            }
            records.append(ref)
            pprint(rec)
            genes, effects = self.split_gene_effects(rec['effectGene'])
            alt = {
                'chrom': rec['chrom'],
                'position': rec['position'],
                'reference': rec['reference'],
                'alternative': rec['alternative'],
                'summary_variant_index': index,
                'allele_index': 1,
                'effect_type': rec['effectType'],
                'effect_gene_genes': genes,
                'effect_gene_types': effects,
                'effect_details_transcript_ids': rec['effectDetails'],
                'effect_details_details': rec['effectDetails'],
                'af_parents_called_count': rec['all.nParCalled'],
                'af_parents_called_percent': rec['all.prcntParCalled'],
                'af_allele_count': rec['all.nAltAlls'],
                'af_allele_freq': rec['all.altFreq'],
            }
            records.append(alt)

        annot_df = pd.DataFrame.from_records(
            data=records,
            columns=[
                'chrom', 'position', 'reference', 'alternative',
                'summary_variant_index',
                'allele_index',
                'effect_type',
                'effect_gene_genes',
                'effect_gene_types',
                'effect_details_transcript_ids',
                'effect_details_details',
                'af_parents_called_count',
                'af_parents_called_percent',
                'af_allele_count',
                'af_allele_freq',
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
