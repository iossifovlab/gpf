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

from dae.pedigrees.pedigree_reader import PedigreeReader

from dae.variants.attributes import VariantType
from dae.variants.family import FamiliesBase, Family
from dae.variants.family_variant import FamilyVariant
from dae.variants.variant import SummaryVariantFactory, SummaryVariant

from dae.utils.vcf_utils import best2gt, str2mat, reference_genotype
from dae.utils.dae_utils import dae2vcf_variant


class BaseDAE(FamiliesBase):

    def __init__(self, family_filename,
                 transmission_type,
                 genome, annotator):
        super(BaseDAE, self).__init__()

        assert genome is not None
        self.transmission_type = transmission_type
        self.family_filename = family_filename

        self.genome = genome
        self.annotator = annotator

    def is_empty(self):
        return False

    def load_pedigree_families(self):
        self.ped_df = PedigreeReader.load_pedigree_file(
            self.family_filename)
        self.families_build(self.ped_df, Family)

    def load_simple_families(self):
        self.ped_df = FamiliesBase.load_simple_family_file(
            self.family_filename)
        self.families_build(self.ped_df, Family)

    def dae2vcf_variant(self, chrom, position, dae_variant):
        position, reference, alternative = dae2vcf_variant(
            chrom, position, dae_variant, self.genome
        )
        return chrom, position, reference, alternative

    @staticmethod
    def split_gene_effects(data, sep="|"):
        if data == 'intergenic':
            return [u'intergenic'], [u'intergenic']

        res = [ge.split(':') for ge in data.split(sep)]
        genes = [str(ge[0]) for ge in res]
        effects = [str(ge[1]) for ge in res]
        return genes, effects

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

    def summary_variant_from_dae_record(self, rec, transmission_type):

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
            ref, transmission_type=transmission_type)

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
        if self.annotator:
            self.annotator.line_annotation(alt)

        alt_allele = SummaryVariantFactory.summary_allele_from_record(
            alt, transmission_type=transmission_type)
        assert alt_allele is not None

        return SummaryVariant([ref_allele, alt_allele])

    def get_reference_genotype(self, family):
        assert family is not None
        return reference_genotype(len(family))


class RawDAE(BaseDAE):

    def __init__(self, summary_filename, toomany_filename, family_filename,
                 region=None, genome=None, annotator=None,
                 transmission_type='transmitted'):
        super(RawDAE, self).__init__(
            family_filename=family_filename,
            transmission_type=transmission_type,
            genome=genome,
            annotator=annotator)

        os.path.exists(summary_filename)
        os.path.exists(toomany_filename)
        os.path.exists(family_filename)

        self.summary_filename = summary_filename
        self.toomany_filename = toomany_filename
        self.region = region

    @staticmethod
    def load_column_names(filename):
        with gzip.open(filename) as infile:
            column_names = \
                infile.readline().decode('utf-8').strip().split("\t")
        return column_names

    @staticmethod
    def explode_family_genotypes(family_data, col_sep="", row_sep="/"):
        res = {
            fid: bs for [fid, bs] in [
                fg.split(':')[:2] for fg in family_data.split(';')]
        }
        res = {
            fid: best2gt(str2mat(bs, col_sep=col_sep, row_sep=row_sep))
            for fid, bs in list(res.items())
        }
        return res

    def load_toomany_columns(self):
        columns = RawDAE.load_column_names(self.toomany_filename)
        return self._rename_columns(columns)

    def load_summary_columns(self):
        summary_columns = RawDAE.load_column_names(self.summary_filename)
        return self._rename_columns(summary_columns)

    def full_variants_iterator(self, return_reference=False):
        summary_columns = self.load_summary_columns()
        toomany_columns = self.load_toomany_columns()

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
                chrom, position, reference, alternative = self.dae2vcf_variant(
                    rec['chrom'], rec['cshl_position'], rec['cshl_variant']
                )
                rec['chrom'] = chrom
                rec['position'] = position
                rec['reference'] = reference
                rec['alternative'] = alternative
                rec['all.nParCalled'] = int(rec['all.nParCalled'])
                rec['all.nAltAlls'] = int(rec['all.nAltAlls'])
                rec['all.prcntParCalled'] = float(rec['all.prcntParCalled'])
                rec['all.altFreq'] = float(rec['all.altFreq'])
                rec['summary_variant_index'] = summary_index

                summary_variant = self.summary_variant_from_dae_record(
                    rec, transmission_type='transmitted')
                family_data = rec['familyData']
                if family_data == 'TOOMANY':
                    toomany_line = next(toomany_iterator)
                    toomany_rec = dict(zip(toomany_columns, toomany_line))
                    family_data = toomany_rec['familyData']

                    assert rec['cshl_position'] == \
                        int(toomany_rec['cshl_position'])
                family_genotypes = self.explode_family_genotypes(family_data)
                family_variants = []
                for family_id in self.family_ids:
                    family = self.families.get(family_id)
                    assert family is not None

                    gt = family_genotypes.get(family_id, None)
                    if gt is None:
                        if not return_reference:
                            continue
                        gt = self.get_reference_genotype(family)

                    assert len(family) == gt.shape[1], family.family_id

                    family_variants.append(
                        FamilyVariant.from_sumary_variant(
                            summary_variant, family, gt))
                yield summary_variant, family_variants


class RawDenovo(BaseDAE):
    def __init__(self, denovo_filename, family_filename,
                 genome=None,
                 annotator=None):
        super(RawDenovo, self).__init__(
            family_filename=family_filename,
            transmission_type='denovo',
            genome=genome,
            annotator=annotator
        )

        os.path.exists(denovo_filename)
        os.path.exists(family_filename)

        assert genome is not None

        self.denovo_filename = denovo_filename
        self.family_filename = family_filename

        self.genome = genome

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
                'familyId': np.str,
                'chr': np.str,
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

    def full_variants_iterator(self, return_reference=False):

        df = self.load_denovo_variants()

        for index, row in df.iterrows():
            row['summary_variant_index'] = index
            try:
                summary_variant = self.summary_variant_from_dae_record(
                    row, transmission_type='denovo')

                gt = self.explode_family_genotype(
                    row['family_data'], col_sep=" ")
                family_id = row['familyId']

                family = self.families.get(family_id)
                assert family is not None

                assert len(family) == gt.shape[1], \
                    (family.family_id, len(family), gt.shape)

                family_variant = FamilyVariant.from_sumary_variant(
                    summary_variant, family, gt)

                yield summary_variant, [family_variant]
            except Exception as ex:
                print("unexpected error:", ex)
                print("error in handling:", row, index)
                traceback.print_exc(file=sys.stdout)
