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

from dae.pedigrees.family import FamiliesData
from dae.variants.variant import SummaryVariantFactory

from dae.backends.raw.loader import VariantsLoader, \
    TransmissionType, FamiliesGenotypes

from dae.variants.attributes import VariantType


class DenovoFamiliesGenotypes(FamiliesGenotypes):

    def __init__(self, family, gt):
        super(DenovoFamiliesGenotypes, self).__init__()
        self.family = family
        self.gt = gt

    def get_family_genotype(self, family):
        return self.gt

    def family_genotype_iterator(self):
        yield self.family, self.gt


class DenovoLoader(VariantsLoader):

    def __init__(
            self, families, denovo_filename, genome, denovo_format={}):
        super(DenovoLoader, self).__init__(
            families=families,
            transmission_type=TransmissionType.denovo)

        assert os.path.exists(denovo_filename)
        self.genome = genome
        self.denovo_format = denovo_format
        self.denovo_filename = denovo_filename

        self.denovo_df = self.flexible_denovo_load(
            self.denovo_filename, genome, **denovo_format
        )

    def summary_genotypes_iterator(self):

        for index, rec in enumerate(self.denovo_df.to_dict(orient='records')):
            rec['summary_variant_index'] = index
            rec['allele_index'] = 1

            summary_variant = SummaryVariantFactory \
                .summary_variant_from_records(
                    [rec], transmission_type=self.transmission_type)
            family_id = rec['family_id']
            gt = rec['genotype']
            family = self.families.get_family(family_id)

            yield summary_variant, DenovoFamiliesGenotypes(family, gt)

    @staticmethod
    def split_location(location):
        chrom, position = location.split(":")
        return chrom, int(position)

    @staticmethod
    def produce_genotype(family, members_with_variant):
        genotype = np.zeros(shape=(2, len(family)), dtype=GENOTYPE_TYPE)
        members_with_variant_index = family.members_index(members_with_variant)
        for index in members_with_variant_index:
            genotype[1, index] = 1
        return genotype

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
            '--denovo-person-id',
            help='The label or index of the column containing the '
            'person\'s ID.',
        )
        parser.add_argument(
            '--denovo-family-id',
            help='The label or index of the column containing the '
            'family\'s ID.',
        )
        parser.add_argument(
            '--denovo-best-state',
            help='The label or index of the column containing the best state'
            ' for the family.',
        )

    @classmethod
    def flexible_denovo_load(
            cls,
            filepath,
            genome,
            location=None,
            variant=None,
            chrom=None,
            pos=None,
            ref=None,
            alt=None,
            person_id=None,
            family_id=None,
            best_state=None,
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

        :param str person_id: The label or index of the column containing
        either
        a singular person ID or a comma-separated list of person IDs.

        :param str family_id: The label or index of the column containing a
        singular family ID.

        :param str best_state: The label or index of the column containing the
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

        if not ((person_id and families) or (family_id and best_state)):
            family_id = 'familyId'
            best_state = 'bestState'

        if families:
            assert isinstance(families, FamiliesData), \
                'families must be an instance of FamiliesData!'

        raw_df = pd.read_csv(
            filepath,
            sep=sep,
            dtype={
                chrom: str,
                pos: int,
                person_id: str,
                family_id: str,
                best_state: str,
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
            pos_col, ref_col, alt_col = zip(*ref_alt_tuples)

        else:
            ref_col = raw_df.loc[:, ref]
            alt_col = raw_df.loc[:, alt]

        if person_id:
            temp_df = pd.DataFrame({
                'chrom': chrom_col,
                'pos': pos_col,
                'ref': ref_col,
                'alt': alt_col,
                'person_id': raw_df.loc[:, person_id],
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
                    temp_df.iloc[variants_indices].loc[:, 'person_id'])\
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
            family_col = raw_df.loc[:, family_id]
            str2mat_partial = partial(str2mat, col_sep=' ')
            genotype_col = map(str2mat_partial, raw_df[best_state])

        return pd.DataFrame({
            'chrom': chrom_col,
            'position': pos_col,
            'reference': ref_col,
            'alternative': alt_col,
            'family_id': family_col,
            'genotype': genotype_col,
        })


class DaeTransmittedFamiliesGenotypes(FamiliesGenotypes):

    def __init__(self, families, families_genotypes):
        super(DaeTransmittedFamiliesGenotypes, self).__init__()
        self.families = families
        self.families_genotypes = families_genotypes

    def get_family_genotype(self, family):
        gt = self.families_genotypes.get(family.family_id, None)
        if gt is not None:
            return gt
        else:
            # FIXME: what genotype we should return in case
            # we have no data in the file:
            # - reference
            # - unknown
            return reference_genotype(len(family))

    def family_genotype_iterator(self):
        for family_id, gt in self.families_genotypes:
            fam = self.families.get_family(family_id)
            yield fam, gt

    def full_families_genotypes(self):

        return self.families_genotypes


class DaeTransmittedLoader(VariantsLoader):

    def __init__(
            self, families,
            summary_filename, toomany_filename, genome,
            region=None,
            include_reference=False):
        super(DaeTransmittedLoader, self).__init__(
            families=families,
            transmission_type=TransmissionType.transmitted)

        assert os.path.exists(summary_filename), summary_filename
        assert os.path.exists(toomany_filename), toomany_filename

        self.summary_filename = summary_filename
        self.toomany_filename = toomany_filename

        self.genome = genome
        self.region = region
        self.include_reference = include_reference

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

    def _summary_variant_from_dae_record(self, summary_index, rec):
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
        summary_variant = SummaryVariantFactory.summary_variant_from_records(
            [ref, alt], transmission_type=self.transmission_type
        )
        return summary_variant

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

    def summary_genotypes_iterator(self):

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

                summary_variant = self._summary_variant_from_dae_record(
                    summary_index, rec)

                family_data = rec['familyData']
                if family_data == 'TOOMANY':
                    toomany_line = next(toomany_iterator)
                    toomany_rec = dict(zip(toomany_columns, toomany_line))
                    family_data = toomany_rec['familyData']

                    assert rec['cshl_position'] == \
                        int(toomany_rec['cshl_position'])
                families_genotypes = DaeTransmittedFamiliesGenotypes(
                    self._explode_family_genotypes(family_data))

                yield summary_variant, families_genotypes
