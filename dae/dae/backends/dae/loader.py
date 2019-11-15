import sys
import traceback
import os
import gzip

from functools import partial
from contextlib import closing

import pysam
import numpy as np
import pandas as pd

from dae.utils.vcf_utils import best2gt, str2mat, GENOTYPE_TYPE, \
    reference_genotype
from dae.utils.dae_utils import dae2vcf_variant
from dae.utils.helpers import pedigree_from_path

from dae.pedigrees.family import FamiliesData
from dae.pedigrees.pedigree_reader import PedigreeReader
from dae.backends.raw.loader import RawVariantsLoader
from dae.backends.dae.raw_dae import RawDenovo, RawDAE

from dae.variants.attributes import VariantType


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

    @classmethod
    def _augment_denovo_variant(cls, denovo_df, genome):
        result = []

        for index, row in denovo_df.iterrows():
            try:
                chrom, cshl_position = cls.split_location(row['location'])

                gt = cls.explode_family_genotype(
                    row['family_data'], col_sep=" ")

                chrom, position, reference, alternative = \
                    cls.dae2vcf_variant(
                        chrom, cshl_position, row['cshl_variant'], genome)
                result.append({
                    'chrom': chrom,
                    'position': position,
                    'reference': reference,
                    'alternative': alternative,
                    'cshl_position': cshl_position,
                    'genotype': gt,
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
                    'genotype': None})

        aug_df = pd.DataFrame.from_records(
            data=result,
            columns=['chrom', 'position',
                     'reference',
                     'alternative',
                     'cshl_position',
                     'genotype'])

        assert len(aug_df.index) == len(denovo_df.index)  # FIXME:

        denovo_df['chrom'] = aug_df['chrom']
        denovo_df['position'] = aug_df['position'].astype(np.int64)
        denovo_df['reference'] = aug_df['reference']
        denovo_df['alternative'] = aug_df['alternative']
        denovo_df['cshl_position'] = aug_df['cshl_position'].astype(np.int64)
        denovo_df['genotype'] = aug_df['genotype']
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
            'familyId': 'family_id',
        })

        return RawDaeLoader._augment_denovo_variant(df, genome)

    @staticmethod
    def build_raw_denovo(ped_df, denovo_df, annot_df=None):
        if annot_df is None:
            annot_df = RawDaeLoader._build_initial_annotation(denovo_df)
        families = FamiliesData.from_pedigree_df(ped_df)

        return RawDenovo(families, denovo_df, annot_df)

    @staticmethod
    def _build_initial_annotation(denovo_df):
        records = []
        for index, rec in enumerate(denovo_df.to_dict(orient='records')):
            records.append(
                (
                    rec['chrom'], rec['position'],
                    rec['reference'], rec['alternative'],
                    index,
                    1, 1
                    ))
        annot_df = pd.DataFrame.from_records(
            data=records,
            columns=[
                'chrom', 'position', 'reference', 'alternative',
                'summary_variant_index',
                'allele_index', 'allele_count',
            ])
        return annot_df

    @classmethod
    def load_raw_denovo_variants(
            cls, pedigree, denovo_filename,
            annotation_filename,
            genome,
            family_format='pedigree',
            pedigree_format={},
            denovo_format={}):

        if isinstance(pedigree, pd.DataFrame):
            ped_df = pedigree
        else:
            family_filename = pedigree
            if family_format == 'pedigree':
                ped_df = PedigreeReader.flexible_pedigree_read(
                    family_filename, **pedigree_format)
            elif family_format == 'simple':
                ped_df = PedigreeReader.load_simple_family_file(
                    family_filename
                )

        if not denovo_format:
            denovo_df = RawDaeLoader.load_dae_denovo_file(
                denovo_filename, genome)
        else:
            denovo_df = RawDaeLoader.flexible_denovo_read(
                denovo_filename, genome,
                **denovo_format
            )

        if annotation_filename is not None \
                and os.path.exists(annotation_filename):
            annot_df = RawDaeLoader.load_annotation_file(annotation_filename)
        else:
            annot_df = RawDaeLoader._build_initial_annotation(denovo_df)

        return RawDaeLoader.build_raw_denovo(ped_df, denovo_df, annot_df)

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

    @classmethod
    def _load_toomany_columns(cls, toomany_filename):
        toomany_columns = cls._load_column_names(toomany_filename)
        return cls._rename_columns(toomany_columns)

    @classmethod
    def _load_summary_columns(cls, summary_filename):
        summary_columns = cls._load_column_names(summary_filename)
        return cls._rename_columns(summary_columns)

    @staticmethod
    def _summary_variant_from_dae_record(rec):
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
        }

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
        }
        return (ref, alt)

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

    @classmethod
    def load_raw_dae_transmitted_variants(
            cls, family_filename, summary_filename, toomany_filename, genome,
            region=None,
            family_format='simple',
            include_reference=False):

        ped_df, _ = pedigree_from_path(
            family_filename, family_format=family_format)
        families = FamiliesData.from_pedigree_df(ped_df)

        summary_columns = cls._load_summary_columns(summary_filename)
        toomany_columns = cls._load_toomany_columns(toomany_filename)

        # using a context manager because of
        # https://stackoverflow.com/a/25968716/2316754
        with closing(pysam.Tabixfile(summary_filename)) as sum_tbf, \
                closing(pysam.Tabixfile(toomany_filename)) as too_tbf:
            summary_iterator = sum_tbf.fetch(
                region=region,
                parser=pysam.asTuple())
            toomany_iterator = too_tbf.fetch(
                region=region,
                parser=pysam.asTuple())

            summary_records = []
            genotype_records = []

            for summary_index, summary_line in enumerate(summary_iterator):
                rec = dict(zip(summary_columns, summary_line))
                rec['cshl_position'] = int(rec['cshl_position'])
                position, reference, alternative = dae2vcf_variant(
                    rec['chrom'], rec['cshl_position'], rec['cshl_variant'],
                    genome
                )
                rec['position'] = position
                rec['reference'] = reference
                rec['alternative'] = alternative
                rec['all.nParCalled'] = int(rec['all.nParCalled'])
                rec['all.nAltAlls'] = int(rec['all.nAltAlls'])
                rec['all.prcntParCalled'] = float(rec['all.prcntParCalled'])
                rec['all.altFreq'] = float(rec['all.altFreq'])
                rec['summary_variant_index'] = summary_index

                ref, alt = cls._summary_variant_from_dae_record(rec)
                summary_records.append(ref)
                summary_records.append(alt)

                family_data = rec['familyData']
                if family_data == 'TOOMANY':
                    toomany_line = next(toomany_iterator)
                    toomany_rec = dict(zip(toomany_columns, toomany_line))
                    family_data = toomany_rec['familyData']

                    assert rec['cshl_position'] == \
                        int(toomany_rec['cshl_position'])
                family_genotypes = cls._explode_family_genotypes(family_data)
                genotype_record = []
                for family in families.families_list():

                    gt = family_genotypes.get(family.family_id, None)
                    if gt is None:
                        gt = reference_genotype(len(family))

                    assert len(family) == gt.shape[1], family.family_id
                    genotype_record.append(gt)
                assert len(genotype_record) == len(families.families_list())
                genotype_records.append(genotype_record)

        annot_df = pd.DataFrame.from_records(summary_records)
        assert len(annot_df) == 2 * len(genotype_records), \
            "{} == 2 * {}".format(len(annot_df), len(genotype_records))

        return RawDAE(families, annot_df, genotype_records)

    @staticmethod
    def flexible_denovo_cli_arguments(parser):
        parser.add_argument(
            '--denovo-location',
            help='The label or index of the column containing the CSHL-style'
                 ' location of the variant.',
        )
        parser.add_argument(
            '--denovo-variant',
            help='The label or index of the column containing the CSHL-style'
                 ' representation of the variant.'
        )
        parser.add_argument(
            '--denovo-chrom',
            help='The label or index of the column containing the chromosome'
                 ' upon which the variant is located.',
        )
        parser.add_argument(
            '--denovo-pos',
            help='The label or index of the column containing the position'
                 ' upon which the variant is located.',
        )
        parser.add_argument(
            '--denovo-ref',
            help='The label or index of the column containing the reference'
                 ' allele for the variant.',
        )
        parser.add_argument(
            '--denovo-alt',
            help='The label or index of the column containing the alternative'
                 ' allele for the variant.',
        )
        parser.add_argument(
            '--denovo-personId',
            help='The label or index of the column containing the '
            'person\'s ID.',
        )
        parser.add_argument(
            '--denovo-familyId',
            help='The label or index of the column containing the '
            'family\'s ID.',
        )
        parser.add_argument(
            '--denovo-bestSt',
            help='The label or index of the column containing the best state'
            ' for the family.',
        )

    @staticmethod
    def produce_genotype(family, members_with_variant):
        genotype = np.zeros(shape=(2, len(family)), dtype=GENOTYPE_TYPE)
        members_with_variant_index = family.members_index(members_with_variant)
        for index in members_with_variant_index:
            genotype[1, index] = 1
        return genotype

    @classmethod
    def flexible_denovo_read(
            cls,
            filepath,
            genome,
            location=None,
            variant=None,
            chrom=None,
            pos=None,
            ref=None,
            alt=None,
            personId=None,
            familyId=None,
            bestSt=None,
            families=None,
            sep='\t'):

        """
        Read a text file containing variants in the form
        of delimiter-separted values and produce a dataframe.

        The text file may use different names for the columns
        containing the relevant data - these are specified
        with the provided parameters.

        :param str filepath: The path to the DSV file to read.

        :param genome: A reference genome object.

        :param str location: The label or index of the column containing the
        CSHL-style location of the variant.

        :param str variant: The label or index of the column containing the
        CSHL-style representation of the variant.

        :param str chrom: The label or index of the column containing the
        chromosome upon which the variant is located.

        :param str pos: The label or index of the column containing the
        position upon which the variant is located.

        :param str ref: The label or index of the column containing the
        variant's reference allele.

        :param str alt: The label or index of the column containing the
        variant's alternative allele.

        :param str personId: The label or index of the column containing either
        a singular person ID or a comma-separated list of person IDs.

        :param str familyId: The label or index of the column containing a
        singular family ID.

        :param str genotype: The label or index of the column containing the
        best state for the variant.

        :param str families: An instance of the FamiliesData class for the
        pedigree of the relevant study.

        :type genome: An instance of GenomicSequence_Dan or
        GenomicSequence_Ivan.

        :return: Dataframe containing the variants, with the following
        header - 'chrom', 'position', 'reference', 'alternative', 'family_id',
        'genotype'.

        :rtype: An instance of Pandas' DataFrame class.
        """

        if not (location or (chrom and pos)):
            location = 'location'

        if not (variant or (ref and alt)):
            variant = 'variant'

        if not ((personId and families) or (familyId and bestSt)):
            familyId = 'familyId'
            bestSt = 'bestState'

        if families:
            assert isinstance(families, FamiliesData), \
                'families must be an instance of FamiliesData!'

        raw_df = pd.read_csv(
            filepath,
            sep=sep,
            dtype={
                chrom: str,
                pos: int,
                personId: str,
                familyId: str,
                bestSt: str,
            }
        )

        if location:
            chrom_col, pos_col = zip(
                *map(cls.split_location, raw_df[location]))
        else:
            chrom_col = raw_df.loc[:, chrom]
            pos_col = raw_df.loc[:, pos]

        if variant:
            assert genome, 'You must provide a genome object!'
            variant_col = raw_df.loc[:, variant]
            ref_alt_tuples = [
                dae2vcf_variant(*variant_tuple, genome)
                for variant_tuple
                in zip(chrom_col, pos_col, variant_col)
            ]
            _, ref_col, alt_col = zip(*ref_alt_tuples)

        else:
            ref_col = raw_df.loc[:, ref]
            alt_col = raw_df.loc[:, alt]

        if personId:
            temp_df = pd.DataFrame({
                'chrom': chrom_col,
                'pos': pos_col,
                'ref': ref_col,
                'alt': alt_col,
                'personId': raw_df.loc[:, personId],
            })

            variant_to_people = dict()
            variant_to_families = dict()

            for variant, variants_indices in \
                    temp_df.groupby(['chrom', 'pos', 'ref', 'alt']) \
                           .groups.items():
                # Here we join and then split again by ',' to handle cases
                # where the person IDs are actually a list of IDs, separated
                # by a ','
                people = ','.join(
                    temp_df.iloc[variants_indices].loc[:, 'personId'])\
                    .split(',')

                variant_to_people[variant] = people
                variant_to_families[variant] = \
                    families.families_query_by_person(people)

            # TODO Implement support for multiallelic variants
            result = []
            for variant, families in variant_to_families.items():
                for family_id, family in families.items():
                    result.append({
                        'chrom': variant[0],
                        'position': variant[1],
                        'reference': variant[2],
                        'alternative': variant[3],
                        'family_id': family_id,
                        'genotype': cls.produce_genotype(
                            family, variant_to_people[variant]
                        )
                    })

            return pd.DataFrame(result)

        else:
            family_col = raw_df.loc[:, familyId]
            str2mat_partial = partial(str2mat, col_sep=' ')
            genotype_col = map(str2mat_partial, raw_df[bestSt])

        return pd.DataFrame({
            'chrom': chrom_col,
            'position': pos_col,
            'reference': ref_col,
            'alternative': alt_col,
            'family_id': family_col,
            'genotype': genotype_col,
        })
