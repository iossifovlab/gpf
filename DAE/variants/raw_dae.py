'''
Created on Jul 23, 2018

@author: lubo
'''
from __future__ import print_function

import gzip
import os
import re

import pysam

import numpy as np
import pandas as pd

from tqdm import tqdm

from variants.attributes import VariantType
from variants.configure import Configure
from variants.family import FamiliesBase, Family
from variants.variant import SummaryVariantFactory, SummaryVariant
from variants.vcf_utils import best2gt, str2mat


from variants.parquet_io import \
    summary_variants_table, family_variants_table
from variants.family_variant import FamilyVariant
<<<<<<< HEAD
from __builtin__ import int
import sys
import traceback
=======
>>>>>>> 0ef39b95fb82e3c6e0dfe149b60af2b9b4a70a7b


class RawDAE(FamiliesBase):

    SUB_RE = re.compile('^sub\(([ACGT])->([ACGT])\)$')
    INS_RE = re.compile('^ins\(([ACGT]+)\)$')
    DEL_RE = re.compile('^del\((\d+)\)$')

    def __init__(self, summary_filename, toomany_filename, family_filename,
                 region=None, genome=None, annotator=None):
        super(RawDAE, self).__init__()
        if region is not None:
            assert isinstance(region, str)

        os.path.exists(summary_filename)
        os.path.exists(toomany_filename)
        os.path.exists(family_filename)

        assert genome is not None

        self.summary_filename = summary_filename
        self.toomany_filename = toomany_filename
        self.region = region
        self.family_filename = family_filename

        self.genome = genome
        self.annotator = annotator

    def load_families(self):
        self.ped_df = FamiliesBase.load_simple_family_file(
            self.family_filename)
        self.families_build(self.ped_df, Family)

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
                region=region,
                parser=pysam.asTuple())  # @UndefinedVariable

            df = pd.DataFrame.from_records(
                data=infile, columns=column_names)

        df['position'] = df['position'].apply(int)

        return df

    @staticmethod
    def load_all(filename):
        with gzip.open(filename) as infile:
            df = pd.read_csv(
                infile,
                dtype={
                    'chr': str,
                    'position': int,
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

        raise NotImplementedError('weird variant: {} at {}:{}'.format(
            dae_variant, chrom, position))

    def augment_cshl_variant(self, df):
        result = []

        for _index, row in df.iterrows():
            try:
                chrom, position, reference, alternative = self.dae2vcf_variant(
                    row['chrom'], row['cshl_position'], row['cshl_variant'])
                result.append({
                    "chrom": chrom,
                    "position": position,
                    "reference": reference,
                    "alternative": alternative})
            except NotImplementedError as ex:
                print("weird variant: ", ex.message)

        aug_df = pd.DataFrame.from_records(
            data=result,
            columns=["chrom", "position", "reference", "alternative"])
        # assert len(aug_df.index) == len(df.index)  FIXME:

        df['position'] = aug_df['position'].astype(np.int64)
        df['reference'] = aug_df['reference']
        df['alternative'] = aug_df['alternative']

        return df

    @staticmethod
    def split_gene_effects(data):
        if data == 'intergenic':
            return [u'intergenic'], [u'intergenic']

        res = [ge.split(':') for ge in data.split(';')]
        genes = [unicode(ge[0], 'utf-8') for ge in res]
        effects = [unicode(ge[1], 'utf-8') for ge in res]
        return genes, effects

    def summary_variant_from_dae_record(self, rec):
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
            'variant_type': 0,
            'cshl_position': rec['cshl_position'],
            'cshl_variant': rec['cshl_variant'],
            'summary_variant_index': rec['summary_variant_index'],
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
        ref_allele = SummaryVariantFactory.summary_allele_from_record(ref)

        genes, effects = self.split_gene_effects(rec['effectGene'])
        effect_details = [unicode(rec['effectDetails'], 'utf-8')]
        alt = {
            'chrom': rec['chrom'],
            'position': rec['position'],
            'reference': rec['reference'],
            'alternative': rec['alternative'],
            'variant_type': VariantType.from_cshl_variant(
                rec['cshl_variant']).value,
            'cshl_position': rec['cshl_position'],
            'cshl_variant': rec['cshl_variant'],
            'summary_variant_index': rec['summary_variant_index'],
            'allele_index': 1,
            'effect_type': rec['effectType'],
            'effect_gene_genes': genes,
            'effect_gene_types': effects,
            'effect_details_transcript_ids': effect_details,
            'effect_details_details': effect_details,
            'af_parents_called_count': rec['all.nParCalled'],
            'af_parents_called_percent': rec['all.prcntParCalled'],
            'af_allele_count': rec['all.nAltAlls'],
            'af_allele_freq': rec['all.altFreq'],
        }
        alt_allele = SummaryVariantFactory.summary_allele_from_record(alt)
        assert alt_allele is not None

        return SummaryVariant([ref_allele, alt_allele])

    def wrap_summary_variants(self, df):
        df['all.nParCalled'] = df['all.nParCalled'].apply(int)
        df['all.nAltAlls'] = df['all.nAltAlls'].apply(int)
        df['all.prcntParCalled'] = df['all.prcntParCalled'].apply(float)
        df['all.altFreq'] = df['all.altFreq'].apply(float)

        with tqdm(len(df)) as pbar:
            for index, row in df.iterrows():
                row['summary_variant_index'] = index
                try:
                    summary_variant = self.summary_variant_from_dae_record(row)
                    pbar.update(1)
                    yield summary_variant
                except Exception as ex:
                    print("unexpected error:", ex)
                    print("error in handling:", row, index)
                    traceback.print_exc(file=sys.stdout)

    def wrap_family_variants(self, df):
        df['all.nParCalled'] = df['all.nParCalled'].apply(int)
        df['all.nAltAlls'] = df['all.nAltAlls'].apply(int)
        df['all.prcntParCalled'] = df['all.prcntParCalled'].apply(float)
        df['all.altFreq'] = df['all.altFreq'].apply(float)

        with tqdm(len(df)) as pbar:

            for index, row in df.iterrows():
                row['summary_variant_index'] = index
                try:
                    summary_variant = self.summary_variant_from_dae_record(row)
                    family_genotypes = self.explode_family_genotypes(
                        row['family_data'])
                    pbar.update(1)

                    for family_id in self.family_ids:
                        family = self.families.get(family_id)
                        assert family is not None

                        gt = family_genotypes.get(family_id, None)
                        if gt is None:
                            gt = self.get_reference_genotype(family)

                        assert len(family) == gt.shape[1], family.family_id

                        family_variant = FamilyVariant(
                            summary_variant, family, gt)
                        yield family_variant
                except Exception as ex:
                    print("unexpected error:", ex)
                    print("error in handling:", row, index)
                    traceback.print_exc(file=sys.stdout)

    def load_variants(self, filename):
        if self.region:
            df = self.load_region(filename, self.region)
        else:
            df = self.load_all(filename)

        df = df.rename(columns={
            "position": "cshl_position",
            "variant": "cshl_variant",
            "chr": "chrom",
        })
        return df

    def load_summary_variants(self):
        df = self.load_variants(self.summary_filename)

        df = self.augment_cshl_variant(df)
        return df

    def merge_family_data(self, df):
        def choose_family_data(row):
            if row['familyData'] == "TOOMANY":
                return row['familyDataToomany']
            return row['familyData']
        family_data = df.apply(choose_family_data, axis=1,
                               result_type='reduce')
        df['family_data'] = family_data
        df = df.drop(columns=["familyData", "familyDataToomany"])
        return df

    @staticmethod
    def explode_family_genotypes(family_data):
        res = {
            fid: bs for [fid, bs] in [
                fg.split(':')[:2] for fg in family_data.split(';')]
        }
        res = {
            fid: best2gt(str2mat(bs)) for fid, bs in res.items()
        }
        return res

    def get_reference_genotype(self, family):
        assert family is not None
        return np.zeros(shape=(2, len(family)), dtype=np.int8)

    def load_family_variants(self):
        summary_df = self.load_variants(self.summary_filename)
        df = self.load_variants(self.toomany_filename)

        vars_df = pd.merge(
            summary_df, df, how="left",
            on=["chrom", "cshl_position", "cshl_variant"],
            suffixes=("", "Toomany"),
            validate="one_to_one")

        vars_df = self.merge_family_data(vars_df)
        vars_df = self.augment_cshl_variant(vars_df)

        return vars_df

    def summary_table(self, df):
        table = summary_variants_table(self.wrap_summary_variants(df))
        return table

    def family_tables(self, df):
        variants = self.wrap_family_variants(df)
        return family_variants_table(variants)


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
