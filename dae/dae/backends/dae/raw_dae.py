'''
Created on Jul 23, 2018

@author: lubo
'''
import gzip
import os
import sys
import traceback
from contextlib import closing

import pysam

import numpy as np
import pandas as pd

from dae.utils.vcf_utils import best2gt, str2mat, reference_genotype
from dae.utils.dae_utils import dae2vcf_variant

from dae.variants.attributes import VariantType
from dae.pedigrees.family import FamiliesData, Family
from dae.variants.family_variant import FamilyVariant
from dae.variants.variant import SummaryVariantFactory, SummaryVariant

from dae.backends.raw.raw_variants import RawFamilyVariants, TransmissionType


class BaseDAE(RawFamilyVariants):

    def __init__(self, families,
                 transmission_type):
        super(BaseDAE, self).__init__(
            families, transmission_type=transmission_type)

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
            'af_parents_called_count': parents_called,
            'af_parents_called_percent':
                float(rec.get('all.prcntParCalled', 0.0)),
            'af_allele_count': ref_allele_count,
            'af_allele_freq': ref_allele_prcnt,
            'transmission_type': self.transmission_type,
        }
        ref_allele = SummaryVariantFactory.summary_allele_from_record(
            ref, transmission_type=self.transmission_type)

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
            'af_parents_called_count': int(rec.get('all.nParCalled', 0)),
            'af_parents_called_percent':
                float(rec.get('all.prcntParCalled', 0.0)),
            'af_allele_count': int(rec.get('all.nAltAlls', 0)),
            'af_allele_freq': float(rec.get('all.altFreq', 0.0)),
            'transmission_type': self.transmission_type,
        }

        alt_allele = SummaryVariantFactory.summary_allele_from_record(
            alt, transmission_type=self.transmission_type)
        assert alt_allele is not None

        return SummaryVariant([ref_allele, alt_allele])




class RawDenovo(BaseDAE):
    def __init__(self, families, denovo_df, annot_df):
        super(RawDenovo, self).__init__(
            families=families,
            transmission_type=TransmissionType.denovo)
        self.denovo_df = denovo_df
        self.annot_df = annot_df

        assert self.annot_df is not None
        assert len(self.denovo_df) == len(self.annot_df)

    def full_variants_iterator(self, return_reference=False):
        denovo = self.denovo_df.to_dict(orient='records')
        annot = self.annot_df.to_dict(orient='records')

        for index, (arow, drow) in enumerate(zip(annot, denovo)):
            try:
                summary_variant = SummaryVariantFactory \
                    .summary_variant_from_records(
                        [arow], transmission_type=self.transmission_type)

                gt = drow['genotype']
                family_id = drow['family_id']
                family = self.families.get_family(family_id)
                assert family is not None

                assert len(family) == gt.shape[1], \
                    (family.family_id, len(family), gt.shape)

                family_variant = FamilyVariant.from_sumary_variant(
                    summary_variant, family, gt)

                yield summary_variant, [family_variant]
            except Exception as ex:
                print("unexpected error:", ex)
                print("error in handling:", arow, drow, index)
                traceback.print_exc(file=sys.stdout)

class RawDAE(BaseDAE):

    def __init__(self, families, summary_filename, toomany_filename,
                 genome, region=None):

        super(RawDAE, self).__init__(
            families,
            transmission_type=TransmissionType.transmitted)

        assert os.path.exists(summary_filename)
        assert os.path.exists(toomany_filename)
        assert genome is not None

        self.summary_filename = summary_filename
        self.toomany_filename = toomany_filename
        self.genome = genome
        self.region = region

    @staticmethod
    def _rename_columns(columns):
        if '#chr' in columns:
            columns[columns.index('#chr')] = 'chrom'
        if 'chr' in columns:
            columns[columns.index('chr')] = 'chrom'
        if 'position' in columns:
            columns[columns.index('position')] = 'cshl_position'
        if 'variant' in columns:
            columns[columns.index('variant')] = 'cshl_variant'
        return columns

    @staticmethod
    def _load_column_names(filename):
        with gzip.open(filename) as infile:
            column_names = \
                infile.readline().decode('utf-8').strip().split("\t")
        return column_names

    @staticmethod
    def _explode_family_genotypes(family_data, col_sep="", row_sep="/"):
        res = {
            fid: bs for [fid, bs] in [
                fg.split(':')[:2] for fg in family_data.split(';')]
        }
        res = {
            fid: best2gt(str2mat(bs, col_sep=col_sep, row_sep=row_sep))
            for fid, bs in list(res.items())
        }
        return res

    @staticmethod
    def _load_toomany_columns(toomany_filename):
        toomany_columns = RawDAE._load_column_names(toomany_filename)
        return RawDAE._rename_columns(toomany_columns)

    @staticmethod
    def load_summary_columns(summary_filename):
        summary_columns = RawDAE.load_column_names(summary_filename)
        return RawDAE._rename_columns(summary_columns)

    def full_variants_iterator(self, return_reference=False):
        summary_columns = self._load_summary_columns(self.summary_filename)
        toomany_columns = self._load_toomany_columns(self.toomany_filename)

        # using a context manager because of
        # https://stackoverflow.com/a/25968716/2316754
        with closing(pysam.Tabixfile(self.summary_filename)) as sum_tbf, \
                closing(pysam.Tabixfile(self.toomany_filename)) as too_tbf:
            summary_iterator = sum_tbf.fetch(
                region=self.region,
                parser=pysam.asTuple())
            toomany_iterator = too_tbf.fetch(
                region=self.region,
                parser=pysam.asTuple())

            for summary_index, summary_line in enumerate(summary_iterator):
                rec = dict(zip(summary_columns, summary_line))
                rec['cshl_position'] = int(rec['cshl_position'])
                position, reference, alternative = dae2vcf_variant(
                    rec['chrom'], rec['cshl_position'], rec['cshl_variant'],
                    self.genome
                )
                rec['position'] = position
                rec['reference'] = reference
                rec['alternative'] = alternative
                rec['all.nParCalled'] = int(rec['all.nParCalled'])
                rec['all.nAltAlls'] = int(rec['all.nAltAlls'])
                rec['all.prcntParCalled'] = float(rec['all.prcntParCalled'])
                rec['all.altFreq'] = float(rec['all.altFreq'])
                rec['summary_variant_index'] = summary_index

                summary_variant = self.summary_variant_from_dae_record(rec)

                family_data = rec['familyData']
                if family_data == 'TOOMANY':
                    toomany_line = next(toomany_iterator)
                    toomany_rec = dict(zip(toomany_columns, toomany_line))
                    family_data = toomany_rec['familyData']

                    assert rec['cshl_position'] == \
                        int(toomany_rec['cshl_position'])
                family_genotypes = self.explode_family_genotypes(family_data)
                family_variants = []
                for family in self.families.families_list():
                    assert family is not None

                    gt = family_genotypes.get(family.family_id, None)
                    if gt is None:
                        if not return_reference:
                            continue
                        gt = reference_genotype(family)

                    assert len(family) == gt.shape[1], family.family_id

                    family_variants.append(
                        FamilyVariant.from_sumary_variant(
                            summary_variant, family, gt))
                yield summary_variant, family_variants
