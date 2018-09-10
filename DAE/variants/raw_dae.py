'''
Created on Jul 23, 2018

@author: lubo
'''
from __future__ import print_function

import gzip
import os
import re
import sys
import traceback

import pysam

import numpy as np
import pandas as pd
from variants.attributes import VariantType
from variants.family import FamiliesBase, Family
from variants.family_variant import FamilyVariant
from variants.variant import SummaryVariantFactory, SummaryVariant
from variants.vcf_utils import best2gt, str2mat, \
    reference_genotype


class BaseDAE(FamiliesBase):
    SUB_RE = re.compile('^sub\(([ACGT])->([ACGT])\)$')
    INS_RE = re.compile('^ins\(([ACGT]+)\)$')
    DEL_RE = re.compile('^del\((\d+)\)$')

    def __init__(self, family_filename,
                 genome=None, annotator=None):
        super(BaseDAE, self).__init__()

        assert genome is not None

        self.family_filename = family_filename

        self.genome = genome
        self.annotator = annotator

    def load_families(self):
        self.ped_df = FamiliesBase.load_simple_family_file(
            self.family_filename)
        self.families_build(self.ped_df, Family)

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

    @staticmethod
    def split_gene_effects(data, sep="|"):
        if data == 'intergenic':
            return [u'intergenic'], [u'intergenic']

        res = [ge.split(':') for ge in data.split(sep)]
        genes = [unicode(ge[0], 'utf-8') for ge in res]
        effects = [unicode(ge[1], 'utf-8') for ge in res]
        return genes, effects

    def summary_variant_from_dae_record(self, rec):
        parents_called = int(rec.get('all.nParCalled', 0))
        ref_allele_count = 2 * int(rec.get('all.nParCalled', 0)) - \
            int(rec.get('all.nAltAlls', 0))
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
            'af_parents_called_percent':
                float(rec.get('all.prcntParCalled', 0.0)),
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
            'af_parents_called_count': int(rec.get('all.nParCalled', 0)),
            'af_parents_called_percent':
                float(rec.get('all.prcntParCalled', 0.0)),
            'af_allele_count': int(rec.get('all.nAltAlls', 0)),
            'af_allele_freq': float(rec.get('all.altFreq', 0.0)),
        }
        alt_allele = SummaryVariantFactory.summary_allele_from_record(alt)
        assert alt_allele is not None

        return SummaryVariant([ref_allele, alt_allele])

    def wrap_summary_variants(self, df):
        for index, row in df.iterrows():
            row['summary_variant_index'] = index
            try:
                summary_variant = self.summary_variant_from_dae_record(row)
                yield summary_variant
            except Exception as ex:
                print("unexpected error:", ex)
                print("error in handling:", row, index)
                traceback.print_exc(file=sys.stdout)

    def get_reference_genotype(self, family):
        assert family is not None
        return reference_genotype(len(family))


class RawDAE(BaseDAE):

    def __init__(self, summary_filename, toomany_filename, family_filename,
                 region=None, genome=None, annotator=None):
        super(RawDAE, self).__init__(
            family_filename=family_filename,
            genome=genome,
            annotator=annotator)

        if region is not None:
            assert isinstance(region, str)

        os.path.exists(summary_filename)
        os.path.exists(toomany_filename)
        os.path.exists(family_filename)

        self.summary_filename = summary_filename
        self.toomany_filename = toomany_filename
        self.region = region

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

    def augment_cshl_variant(self, df):
        result = []

        for index, row in df.iterrows():
            try:
                chrom, position, reference, alternative = self.dae2vcf_variant(
                    row['chrom'], row['cshl_position'], row['cshl_variant'])
                result.append({
                    "chrom": chrom,
                    "position": position,
                    "reference": reference,
                    "alternative": alternative})
            except Exception as ex:
                print("unexpected error:", ex)
                print("error in handling:", row, index)
                traceback.print_exc(file=sys.stdout)
                result.append({
                    "chrom": chrom,
                    "position": row['cshl_position'],
                    "reference": None,
                    "alternative": None})

        aug_df = pd.DataFrame.from_records(
            data=result,
            columns=["chrom", "position", "reference", "alternative"])

        assert len(aug_df.index) == len(df.index)  # FIXME:

        df['position'] = aug_df['position'].astype(np.int64)
        df['reference'] = aug_df['reference']
        df['alternative'] = aug_df['alternative']

        return df

    @staticmethod
    def explode_family_genotypes(family_data, col_sep="", row_sep="/"):
        res = {
            fid: bs for [fid, bs] in [
                fg.split(':')[:2] for fg in family_data.split(';')]
        }
        res = {
            fid: best2gt(str2mat(bs, col_sep=col_sep, row_sep=row_sep))
            for fid, bs in res.items()
        }
        return res

    def wrap_family_variants(self, df, return_reference=False):
        df['all.nParCalled'] = df['all.nParCalled'].apply(int)
        df['all.nAltAlls'] = df['all.nAltAlls'].apply(int)
        df['all.prcntParCalled'] = df['all.prcntParCalled'].apply(float)
        df['all.altFreq'] = df['all.altFreq'].apply(float)

        for index, row in df.iterrows():
            row['summary_variant_index'] = index
            try:
                summary_variant = self.summary_variant_from_dae_record(row)
                family_genotypes = self.explode_family_genotypes(
                    row['family_data'])

                for family_id in self.family_ids:
                    family = self.families.get(family_id)
                    assert family is not None

                    gt = family_genotypes.get(family_id, None)
                    if gt is None:
                        if not return_reference:
                            continue
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


class RawDenovo(BaseDAE):
    def __init__(self, denovo_filename, family_filename,
                 genome=None, annotator=None):
        super(RawDenovo, self).__init__(
            family_filename=family_filename,
            genome=genome,
            annotator=annotator
        )

        os.path.exists(denovo_filename)
        os.path.exists(family_filename)

        assert genome is not None

        self.denovo_filename = denovo_filename
        self.family_filename = family_filename

        self.genome = genome
        self.annotator = annotator

    def split_location(self, location):
        chrom, position = location.split(":")
        return chrom, int(position)

    def augment_denovo_variant(self, df):
        result = []

        for index, row in df.iterrows():
            try:
                chrom, cshl_position = self.split_location(row['location'])

                chrom, position, reference, alternative = self.dae2vcf_variant(
                    chrom, cshl_position, row['cshl_variant'])
                result.append({
                    "chrom": chrom,
                    "position": position,
                    "reference": reference,
                    "alternative": alternative,
                    "cshl_position": cshl_position,
                })
            except Exception as ex:
                print("unexpected error:", ex)
                print("error in handling:", row, index)
                traceback.print_exc(file=sys.stdout)
                result.append({
                    "chrom": chrom,
                    "position": None,
                    "reference": None,
                    "alternative": None})

        aug_df = pd.DataFrame.from_records(
            data=result,
            columns=["chrom", "position",
                     "reference",
                     "alternative",
                     "cshl_position"])

        assert len(aug_df.index) == len(df.index)  # FIXME:

        df['chrom'] = aug_df['chrom']
        df['position'] = aug_df['position'].astype(np.int64)
        df['reference'] = aug_df['reference']
        df['alternative'] = aug_df['alternative']
        df['cshl_position'] = aug_df['cshl_position'].astype(np.int64)
        return df

    def load_denovo_variants(self):
        df = pd.read_csv(
            self.denovo_filename,
            dtype={
                'familyId': str,
                'chr': str,
                'position': int,
            },
            sep='\t')

        df = df.rename(columns={
            "variant": "cshl_variant",
            "bestState": "family_data",
        })
        df = self.augment_denovo_variant(df)
        return df

    @staticmethod
    def explode_family_genotype(best_st, col_sep="", row_sep="/"):
        return best2gt(str2mat(best_st, col_sep=col_sep, row_sep=row_sep))

    def wrap_family_variants(self, df):

        for index, row in df.iterrows():
            row['summary_variant_index'] = index
            try:
                summary_variant = self.summary_variant_from_dae_record(row)
                gt = self.explode_family_genotype(
                    row['family_data'], col_sep=" ")
                family_id = row['familyId']

                family = self.families.get(family_id)
                assert family is not None

                assert len(family) == gt.shape[1], family.family_id

                family_variant = FamilyVariant(
                    summary_variant, family, gt)

                yield family_variant
            except Exception as ex:
                print("unexpected error:", ex)
                print("error in handling:", row, index)
                traceback.print_exc(file=sys.stdout)
