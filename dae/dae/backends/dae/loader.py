import sys
import traceback
import os

import numpy as np
import pandas as pd 

from dae.utils.vcf_utils import best2gt, str2mat, reference_genotype
from dae.utils.dae_utils import dae2vcf_variant

from dae.pedigrees.family import FamiliesData
from dae.pedigrees.pedigree_reader import PedigreeReader
from dae.backends.raw.loader import RawVariantsLoader
from dae.backends.dae.raw_dae import RawDenovo

class RawDaeLoader(RawVariantsLoader):

    @staticmethod
    def split_location(location):
        chrom, position = location.split(":")
        return chrom, int(position)

    @staticmethod
    def explode_family_genotype(best_st, col_sep="", row_sep="/"):
        return best2gt(str2mat(best_st, col_sep=col_sep, row_sep=row_sep))

    @staticmethod
    def dae2vcf_variant(chrom, position, dae_variant, genome):
        position, reference, alternative = dae2vcf_variant(
            chrom, position, dae_variant, genome
        )
        return chrom, position, reference, alternative

    @staticmethod
    def _augment_denovo_variant(denovo_df, genome):
        result = []

        for index, row in denovo_df.iterrows():
            try:
                chrom, cshl_position = RawDaeLoader.split_location(row['location'])

                gt = RawDaeLoader.explode_family_genotype(
                    row['family_data'], col_sep=" ")

                chrom, position, reference, alternative = \
                    RawDaeLoader.dae2vcf_variant(
                        chrom, cshl_position, row['cshl_variant'], genome)
                result.append({
                    'chrom': chrom,
                    'position': position,
                    'reference': reference,
                    'alternative': alternative,
                    'cshl_position': cshl_position,
                    'gt': gt,
                })
            except Exception as ex:
                print("unexpected error:", ex)
                print("error in handling:", row, index)
                traceback.print_exc(file=sys.stdout)
                result.append({
                    'chrom': chrom,
                    'position': None,
                    'reference': None,
                    'alternative': None,
                    'gt': None})

        aug_df = pd.DataFrame.from_records(
            data=result,
            columns=['chrom', 'position',
                     'reference',
                     'alternative',
                     'cshl_position',
                     'gt'])

        assert len(aug_df.index) == len(denovo_df.index)  # FIXME:

        denovo_df['chrom'] = aug_df['chrom']
        denovo_df['position'] = aug_df['position'].astype(np.int64)
        denovo_df['reference'] = aug_df['reference']
        denovo_df['alternative'] = aug_df['alternative']
        denovo_df['cshl_position'] = aug_df['cshl_position'].astype(np.int64)
        denovo_df['gt'] = aug_df['gt']
        return denovo_df

    @staticmethod
    def load_dae_denovo_file(denovo_filename, genome):
        df = pd.read_csv(
            denovo_filename,
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

        return RawDaeLoader._augment_denovo_variant(df, genome)

    @staticmethod
    def build_raw_denovo(ped_df, denovo_df):
        families = FamiliesData.from_pedigree_df(ped_df)

        return RawDenovo(families, denovo_df)

    @staticmethod
    def load_raw_denovo(
            ped_filename, denovo_filename,
            annotation_filename=None, region=None):
        ped_df = PedigreeReader.load_pedigree_file(ped_filename)
        denovo_df = RawDaeLoader.load_dae_denovo_file(denovo_filename, region)

        annot_df = None
        if annotation_filename is not None \
                and os.path.exists(annotation_filename):
            annot_df = RawDaeLoader.load_annotation_file(annotation_filename)
        return RawDaeLoader.build_raw_denovo(ped_df, denovo_df, annot_df)
